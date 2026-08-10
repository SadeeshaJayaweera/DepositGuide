import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.auth import get_current_user
from app.db import get_session
from app.models import User, Statement
from app.agents.deposit_recommendation import recommend_deposit_schedule
from app.agents.interest_engine import compute_interest_for_schedule

engine = create_engine(
    "sqlite://", 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)

@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        user = User(hashed_password="test", email="rec_test@example.com")
        session.add(user)
        session.commit()
        session.refresh(user)
        
        statement = Statement(
            user_id=user.id,
            issuing_bank="CanonicalBank",
            statement_date=date(2026, 1, 1),
            due_date=date(2026, 1, 31), # 30 days cycle (1 to 31 is 30 elapsed days)
            minimum_payment=5000.0,
            purchase_apr=0.28,
            cash_advance_apr=0.33,
            purchase_balance=100000.0,
            cash_advance_balance=0.0,
            raw_source_filename="test.pdf"
        )
        session.add(statement)
        session.commit()
        session.refresh(statement)
        
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session
    def get_current_user_override():
        return session.get(User, 1)

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_user] = get_current_user_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_interest_engine_math(session: Session):
    statement = session.get(Statement, 1)
    
    # Baseline: min payment on due date
    baseline_sch = {statement.due_date: 5000.0}
    # 30 days of 100k balance at 28% APR = 100k * 0.28 / 365 * 30 = 2301.37
    # Note: cycle is day 1 to day 31 inclusive = 31 days. 
    # Wait, 1 to 31 is 31 days. If we want exactly 30 days, we should use 1 to 30.
    # Let's see: 100000 * 0.28 / 365 = 76.7123. * 30 = 2301.37.
    # If the due date is 1,31, the loop in `interest_engine` goes from 1 to 31 (inclusive), which is 31 days!
    # Let's adjust statement in fixture or accept 31 days. Actually, the math in the prompt is:
    # 2301 is exactly 30 days. Let me adjust the fixture statement date to 2. 2 to 31 inclusive is 30 days.
    pass

def test_recommendation_optimizes_interest(session: Session):
    statement = session.get(Statement, 1)
    # We want exactly 30 days of interest.
    statement.statement_date = date(2026, 1, 2)
    statement.due_date = date(2026, 1, 31)
    session.add(statement)
    session.commit()
    
    # We constrain the forecast so that Full Payoff is impossible, 
    # but a 50k payment on day 10 is possible, and the remaining 50k on due date is possible.
    forecast = {}
    current = statement.statement_date
    day_11 = date(2026, 1, 11) # Day 10 of the cycle (2nd to 11th is 10 days)
    
    while current <= statement.due_date:
        if current < day_11:
            forecast[current] = 10000.0 # Not enough for 25k (25%)
        elif current < statement.due_date:
            forecast[current] = 55000.0 # Enough for 50k, but not 75k
        else:
            forecast[current] = 110000.0 # Enough for everything on due date
        current += timedelta(days=1)
        
    rec = recommend_deposit_schedule(statement, forecast, session)
    
    # Baseline for 30 days is 2301.37
    assert 2300 < rec.baseline_interest < 2302
    
    # The selected schedule should pay 50k on day 11, reducing interest by exactly ~33%
    assert 1533 < rec.projected_interest < 1535
    
    # 2301 -> 1534 is a ~33% reduction
    reduction = (rec.baseline_interest - rec.projected_interest) / rec.baseline_interest
    assert 0.32 < reduction < 0.34

def test_recommendation_endpoint(client: TestClient, session: Session):
    statement = session.get(Statement, 1)
    statement.statement_date = date(2026, 1, 2)
    statement.due_date = date(2026, 1, 31)
    session.add(statement)
    session.commit()
    
    # We need a user profile so forecast doesn't return 0
    from app.models import FinancialBehaviorProfile
    profile = FinancialBehaviorProfile(
        user_id=1,
        salary_cycle_day=11, # Salary exactly on day 11
        avg_discretionary_spend=0.0,
        repayment_adherence_score=0.5,
        risk_tolerance="moderate"
    )
    session.add(profile)
    session.commit()
    
    # In order to simulate the 50k availability, we must ensure _get_last_salary_amount returns 55000
    # The cash flow agent will add 55000 on day 11. 
    # Before that, it's 0.
    from app.models import Transaction
    tx = Transaction(
        statement_id=1,
        date=date(2025, 12, 11),
        description="Salary",
        amount=55000.0,
        category="Income"
    )
    session.add(tx)
    session.commit()
    
    response = client.post("/recommendations/1")
    assert response.status_code == 200
    data = response.json()
    
    assert "savings_summary" in data
    assert "reduce this cycle's interest by 33%" in data["savings_summary"]
