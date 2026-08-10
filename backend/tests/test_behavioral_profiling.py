import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import get_session
from app.models import User, Statement, Transaction, FinancialBehaviorProfile
from app.agents.behavioral_profiling import update_profile

engine = create_engine(
    "sqlite://", 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)

@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # Create user
        user = User(hashed_password="test", email="profile_test@example.com")
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # 3 months of statements
        for month in [6, 7, 8]:
            stmt = Statement(
                user_id=user.id,
                issuing_bank="TestBank",
                statement_date=date(2026, month, 1),
                due_date=date(2026, month, 25),
                minimum_payment=100.0,
                purchase_apr=0.20,
                cash_advance_apr=0.25,
                purchase_balance=1000.0,
                cash_advance_balance=0.0,
                raw_source_filename="test.pdf"
            )
            session.add(stmt)
            session.commit()
            session.refresh(stmt)
            
            # Payroll on the 15th (matching keyword 'payroll')
            tx_salary = Transaction(
                statement_id=stmt.id,
                date=date(2026, month, 15),
                description="ACME CORP PAYROLL",
                amount=5000.0, # Large credit
                category="Income"
            )
            session.add(tx_salary)
            
            # Discretionary spend (Dining and Entertainment)
            tx_dining = Transaction(
                statement_id=stmt.id,
                date=date(2026, month, 5),
                description="Restaurant",
                amount=-100.0,
                category="Dining"
            )
            tx_ent = Transaction(
                statement_id=stmt.id,
                date=date(2026, month, 20),
                description="Movie Theater",
                amount=-50.0,
                category="Entertainment"
            )
            
            # Essential spend (should be ignored by avg_discretionary_spend)
            tx_groceries = Transaction(
                statement_id=stmt.id,
                date=date(2026, month, 10),
                description="Grocery Store",
                amount=-200.0,
                category="Groceries"
            )
            
            session.add(tx_dining)
            session.add(tx_ent)
            session.add(tx_groceries)
            session.commit()

        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_update_profile_logic(session: Session):
    # User 1 has 3 months of data, each with -150 non-essential spend
    # Total discretionary spend across 3 months = 450
    # Average = 150
    # Salary day = 15
    profile = update_profile(1, session)
    
    assert profile.salary_cycle_day == 15
    assert profile.avg_discretionary_spend == 150.0
    assert profile.repayment_adherence_score == 0.5
    assert profile.risk_tolerance == "moderate"

def test_refresh_profile_endpoint(client: TestClient):
    response = client.post("/profile/refresh/1")
    assert response.status_code == 200
    data = response.json()
    assert data["salary_cycle_day"] == 15
    assert data["avg_discretionary_spend"] == 150.0

def test_get_profile_endpoint(client: TestClient):
    # Ensure it exists
    client.post("/profile/refresh/1")
    
    response = client.get("/profile/1")
    assert response.status_code == 200
    data = response.json()
    assert data["salary_cycle_day"] == 15

def test_patch_risk_tolerance_endpoint(client: TestClient):
    # Patch without existing profile should create one
    response = client.patch("/profile", json={"user_id": 1, "risk_tolerance": "high"})
    assert response.status_code == 200
    data = response.json()
    assert data["risk_tolerance"] == "high"
    
    # Then refresh profile, risk_tolerance should be preserved
    refresh_response = client.post("/profile/refresh/1")
    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert data["risk_tolerance"] == "high"
    assert data["salary_cycle_day"] == 15
