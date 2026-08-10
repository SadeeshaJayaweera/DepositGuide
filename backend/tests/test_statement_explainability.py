import json
from datetime import date
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
import pytest

from app.main import app
from app.db import get_session
from app.models import Statement, Transaction, User
from app.agents.statement_explainability import explain_statement
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
        user = User(hashed_password="test", email="explain_test@example.com")
        session.add(user)
        session.commit()
        
        # Add dummy statement
        statement = Statement(
            user_id=user.id,
            issuing_bank="TestBank",
            statement_date=date(2026, 8, 1),
            due_date=date(2026, 8, 25),
            minimum_payment=5000.0,
            purchase_apr=0.28,
            cash_advance_apr=0.33,
            purchase_balance=100000.0,
            cash_advance_balance=0.0,
            raw_source_filename="test.pdf"
        )
        session.add(statement)
        session.commit()
        
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="fake_llm")
def fake_llm_fixture():
    # Return a valid JSON matching the Pydantic schema
    canned_response = json.dumps({
        "explanations": [
            {
                "line_item_name": "Purchase Balance",
                "plain_language_explanation": "You owe 100000.0."
            }
        ]
    })
    return FakeLLMClient(canned_response=canned_response)

@pytest.fixture(name="client")
def client_fixture(session: Session, fake_llm: FakeLLMClient):
    def get_session_override():
        return session
    
    def get_llm_client_override():
        return fake_llm

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_llm_client] = get_llm_client_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_explain_statement_logic(fake_llm):
    statement = Statement(
        user_id=1,
        issuing_bank="TestBank",
        statement_date=date(2026, 8, 1),
        due_date=date(2026, 8, 25),
        minimum_payment=5000.0,
        purchase_apr=0.28,
        cash_advance_apr=0.33,
        purchase_balance=100000.0,
        cash_advance_balance=0.0,
        raw_source_filename="test.pdf"
    )
    interest_breakdown = {
        "projected_interest": 1500.0,
        "baseline_interest": 50.0
    }
    
    result = explain_statement(statement, [], interest_breakdown, fake_llm)
    
    # Assert JSON parsing worked
    assert len(result.explanations) == 1
    assert result.explanations[0].line_item_name == "Purchase Balance"
    
    # Assert numerical grounding in prompt
    assert "Purchase Balance: 100000.0" in fake_llm.last_user_prompt
    assert "Purchase APR: 0.28" in fake_llm.last_user_prompt
    assert "Projected Interest: 1500.0" in fake_llm.last_user_prompt
    
    # Assert strict instructions in system prompt
    assert "Do NOT invent, guess, or round any numbers" in fake_llm.last_system_prompt

def test_explain_statement_endpoint(client: TestClient, session: Session):
    # statement id 1 was created in the fixture
    response = client.get("/statements/1/explain")
    assert response.status_code == 200
    
    data = response.json()
    assert "explanations" in data
    assert len(data["explanations"]) == 1
    assert data["explanations"][0]["line_item_name"] == "Purchase Balance"

def test_system_prompt_forbids_inventing_figures(fake_llm):
    """Guards against silent regressions in the prompt that would allow the LLM to hallucinate numbers."""
    statement = Statement(
        user_id=1,
        issuing_bank="TestBank",
        statement_date=date(2026, 8, 1),
        due_date=date(2026, 8, 25),
        minimum_payment=5000.0,
        purchase_apr=0.28,
        cash_advance_apr=0.33,
        purchase_balance=100000.0,
        cash_advance_balance=0.0,
        raw_source_filename="test.pdf"
    )
    interest_breakdown = {}
    
    explain_statement(statement, [], interest_breakdown, fake_llm)
    
    system_prompt_lower = fake_llm.last_system_prompt.lower()
    
    assert "invent" in system_prompt_lower, "System prompt must forbid inventing figures"
    assert "guess" in system_prompt_lower, "System prompt must forbid guessing figures"
    assert "round" in system_prompt_lower, "System prompt must forbid rounding figures"
