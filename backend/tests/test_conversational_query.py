import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
import json

from app.main import app
from app.auth import get_current_user
from app.db import get_session
from app.models import User, Statement, FinancialBehaviorProfile, DepositRecommendation
from app.agents.conversational_query import answer_question
from app.llm.client import FakeLLMClient, get_llm_client

engine = create_engine(
    "sqlite://", 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)

@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        user = User(hashed_password="test", email="chat_test@example.com")
        session.add(user)
        session.commit()
        session.refresh(user)
        
        statement = Statement(
            user_id=user.id,
            issuing_bank="ChatBank",
            statement_date=date(2026, 1, 1),
            due_date=date(2026, 1, 31),
            minimum_payment=5000.0,
            purchase_apr=0.28,
            cash_advance_apr=0.33,
            purchase_balance=100000.0,
            cash_advance_balance=0.0,
            raw_source_filename="chat.pdf"
        )
        session.add(statement)
        session.commit()
        session.refresh(statement)
        
        profile = FinancialBehaviorProfile(
            user_id=user.id,
            salary_cycle_day=15,
            avg_discretionary_spend=500.0,
            repayment_adherence_score=0.8,
            risk_tolerance="high"
        )
        session.add(profile)
        
        schedule = {"2026-01-10": 50000.0, "2026-01-31": 50000.0}
        rec = DepositRecommendation(
            user_id=user.id,
            statement_id=statement.id,
            schedule_json=json.dumps(schedule),
            projected_interest=1534.0,
            baseline_interest=2301.0
        )
        session.add(rec)
        session.commit()
        
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="fake_llm")
def fake_llm_fixture():
    return FakeLLMClient(canned_response="I am grounded in your context.")

@pytest.fixture(name="client")
def client_fixture(session: Session, fake_llm: FakeLLMClient):
    def get_session_override():
        return session
    def get_llm_client_override():
        return fake_llm
    def get_current_user_override():
        return session.get(User, 1)
    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_llm_client] = get_llm_client_override
    app.dependency_overrides[get_current_user] = get_current_user_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_answer_question_context_injection(session: Session, fake_llm: FakeLLMClient):
    answer = answer_question(1, "What is my balance?", session, fake_llm)
    
    assert answer == "I am grounded in your context."
    
    # Assert context is properly injected into the system prompt
    assert "100000.0" in fake_llm.last_system_prompt
    assert "2026-01-31" in fake_llm.last_system_prompt
    assert "high" in fake_llm.last_system_prompt  # risk_tolerance
    assert "1534.0" in fake_llm.last_system_prompt # projected_interest
    
    # Assert question is passed properly
    assert "What is my balance?" in fake_llm.last_user_prompt
    
    # Assert strict instructions
    assert "politely refuse" in fake_llm.last_system_prompt
    assert "ONLY using the provided context" in fake_llm.last_system_prompt

def test_chat_endpoint(client: TestClient, fake_llm: FakeLLMClient):
    response = client.post("/chat", json={"question": "Can I afford this?"})
    assert response.status_code == 200
    assert response.json() == {"answer": "I am grounded in your context."}
