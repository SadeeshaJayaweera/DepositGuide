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
    # 0. Register & Login
    reg_resp = client.post("/auth/register", json={"email": "test@example.com", "password": "password"})
    assert reg_resp.status_code == 200
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Upload
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    pdf_path = os.path.join(fixtures_dir, "sample_statement_bank_b.pdf")
    
    with open(pdf_path, "rb") as f:
        upload_resp = client.post(
            "/statements/upload",
            headers=headers,
            data={"issuing_bank": "pdfbank"},
            files={"file": ("sample_statement_bank_b.pdf", f, "application/pdf")}
        )
    assert upload_resp.status_code == 200, upload_resp.text
    upload_data = upload_resp.json()
    statement_id = upload_data["statement_id"]
    
    # 2. Explain
    explain_resp = client.get(f"/statements/{statement_id}/explain", headers=headers)
    assert explain_resp.status_code == 200, explain_resp.text
    assert len(explain_resp.json()["explanations"]) > 0
    
    from app.models import Transaction, Statement
    stmt = session.get(Statement, statement_id)
    stmt.statement_date = date(2026, 8, 1)
    stmt.due_date = date(2026, 8, 30)
    session.add(stmt)
    
    tx = Transaction(
        statement_id=statement_id,
        date=date(2026, 8, 10),
        description="Salary",
        amount=55000.0,
        category="Income"
    )
    session.add(tx)
    session.commit()
    
    # 3. Profile Refresh
    profile_resp = client.post("/profile/refresh", headers=headers)
    assert profile_resp.status_code == 200
    
    # 5. Deposit Recommendation
    rec_resp = client.post(f"/recommendations/{statement_id}", headers=headers)
    assert rec_resp.status_code == 200, rec_resp.text
    rec_data = rec_resp.json()
    
    assert "reduce this cycle's interest by 33%" in rec_data["savings_summary"]
    
    # 6. Chat
    chat_resp = client.post("/chat", headers=headers, json={"question": "What is my recommendation?"})
    assert chat_resp.status_code == 200
    assert chat_resp.json()["answer"] == "I am grounded in your context."
