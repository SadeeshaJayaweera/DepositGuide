import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.auth import get_current_user
from app.db import get_session
from app.models import User, FinancialBehaviorProfile
from app.agents.cash_flow_forecast import forecast_available_funds

engine = create_engine(
    "sqlite://", 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)

@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        user = User(hashed_password="test", email="forecast_test@example.com")
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Profile: salary on the 15th, 300 avg spend (10/day)
        profile = FinancialBehaviorProfile(
            user_id=user.id,
            salary_cycle_day=15,
            avg_discretionary_spend=300.0,
            repayment_adherence_score=0.5,
            risk_tolerance="moderate"
        )
        session.add(profile)
        session.commit()
        
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

def test_forecast_available_funds_curve_shape(session: Session):
    # start_date in logic is today. We will generate candidate dates for the current month
    today = date.today()
    
    # We'll generate dates from today until 30 days out
    candidate_dates = [today + timedelta(days=i) for i in range(30)]
    
    forecasts = forecast_available_funds(1, candidate_dates, session)
    
    # Let's find specific dates:
    # Our stub bill is on the 10th of the start_date's month
    try:
        bill_date = date(today.year, today.month, 10)
    except ValueError:
        return # Skip if month weirdness
        
    if bill_date >= today:
        day_before_bill = bill_date - timedelta(days=1)
        day_after_bill = bill_date + timedelta(days=1)
        
        if day_before_bill in forecasts and day_after_bill in forecasts:
            # Funds should drop after the bill
            assert forecasts[day_after_bill] < forecasts[day_before_bill]
            
    # Salary is on the 15th
    try:
        salary_date = date(today.year, today.month, 15)
    except ValueError:
        return
        
    if salary_date >= today:
        day_before_salary = salary_date - timedelta(days=1)
        day_after_salary = salary_date + timedelta(days=1)
        
        if day_before_salary in forecasts and day_after_salary in forecasts:
            # Funds should rise significantly after salary
            assert forecasts[day_after_salary] > forecasts[day_before_salary]

