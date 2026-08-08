import os
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
import json

from app.main import app
from app.db import get_session
from app.models import User
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
        yield session
    SQLModel.metadata.drop_all(engine)

class E2EFakeLLMClient(FakeLLMClient):
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        if "line_item_name" in system_prompt or "plain-language" in system_prompt:
            return json.dumps({
                "explanations": [
                    {"line_item_name": "Test Item", "plain_language_explanation": "Test explanation"}
                ]
            })
        return "I am grounded in your context."

@pytest.fixture(name="fake_llm")
def fake_llm_fixture():
    return E2EFakeLLMClient()

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

def test_full_pipeline_produces_33_percent_savings(client: TestClient, session: Session):
    """
    Simulates the entire 6-step flow of DepositGuide.
    1. Upload Statement
    2. Explain
    3. Profile Refresh
    4. Cash-Flow Forecast
    5. Deposit Recommendation
    6. Chat
    """
    
    # 1. Upload
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    pdf_path = os.path.join(fixtures_dir, "sample_statement_bank_b.pdf")
    
    with open(pdf_path, "rb") as f:
        upload_resp = client.post(
            "/statements/upload",
            data={"issuing_bank": "pdfbank"},
            files={"file": ("sample_statement_bank_b.pdf", f, "application/pdf")}
        )
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    statement_id = upload_data["statement_id"]
    
    # The user was created dynamically in the upload endpoint
    user = session.exec(SQLModel.metadata.tables["user"].select()).first()
    # Or simply we know user_id = 1
    user_id = 1
    
    # 2. Explain
    explain_resp = client.get(f"/statements/{statement_id}/explain")
    assert explain_resp.status_code == 200, f"Explain endpoint failed: {explain_resp.text}"
    assert len(explain_resp.json()["explanations"]) > 0
    
    # In order for cash flow to be sufficient for an early 50k payment, 
    # we need to inject a salary transaction before day 10, or just have a large balance.
    # The pdfbank parser returns a transaction on 2026-08-01 of 55000.
    # Let's manually ensure the profile gets created with an early salary day, 
    # and the forecast sees sufficient funds.
    # Wait, pdfbank fixture returns:
    # tx 0: 2026-08-01, 15000 (Grocery)
    # tx 1: 2026-08-01, 25000 (Salary/Income?)
    # The pdfbank parser might just have random descriptions. 
    # If the forecast relies on "salary/payroll", we should just inject one transaction 
    # to guarantee the 33% reduction math (like in test_deposit_recommendation.py).
    from app.models import Transaction, Statement
    stmt = session.get(Statement, statement_id)
    # We want a 30-day cycle for the 33% math: 2026-08-01 to 2026-08-30.
    # The pdfbank parser has due_date 2026-08-25 (24 days). 
    # Let's adjust statement dates slightly for the perfect math test.
    stmt.statement_date = date(2026, 8, 1)
    stmt.due_date = date(2026, 8, 30)
    session.add(stmt)
    
    tx = Transaction(
        statement_id=statement_id,
        date=date(2026, 8, 10), # Day 10 of the cycle
        description="Salary",
        amount=55000.0,
        category="Income"
    )
    session.add(tx)
    session.commit()
    
    # 3. Profile Refresh
    profile_resp = client.post(f"/profile/refresh/{user_id}")
    assert profile_resp.status_code == 200
    
    # 4. Cash-Flow Forecast (The recommendation endpoint calls this internally, 
    # but let's test the endpoint directly first)
    forecast_resp = client.get(f"/cashflow/forecast/{user_id}?candidate_dates=2026-08-10&candidate_dates=2026-08-11")
    assert forecast_resp.status_code == 200
    
    # 5. Deposit Recommendation
    rec_resp = client.post(f"/recommendations/{statement_id}")
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    
    # Verify the paper's ~33% interest reduction
    assert "reduce this cycle's interest by 33%" in rec_data["savings_summary"]
    
    # 6. Chat
    chat_resp = client.post(f"/chat/{user_id}", json={"question": "What is my recommendation?"})
    assert chat_resp.status_code == 200
    assert chat_resp.json()["answer"] == "I am grounded in your context."
