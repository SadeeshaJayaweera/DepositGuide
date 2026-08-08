import os
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import get_session
from app.models import Statement, Transaction, User
from app.agents.statement_parsing import ParserRegistry, ParsedStatement

# Setup in-memory sqlite for testing
engine = create_engine(
    "sqlite://", 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)

@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # Create default test user
        user = User(email="test@example.com")
        session.add(user)
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

def test_csv_parser():
    parser = ParserRegistry.get_parser("csvbank")
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    csv_path = os.path.join(fixtures_dir, "sample_statement_bank_a.csv")
    
    with open(csv_path, "rb") as f:
        parsed = parser.parse(f.read())
        
    assert isinstance(parsed, ParsedStatement)
    assert parsed.issuing_bank == "CsvBank"
    assert len(parsed.transactions) == 3
    assert parsed.transactions[0].amount == 150.0

def test_pdf_parser():
    parser = ParserRegistry.get_parser("pdfbank")
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    pdf_path = os.path.join(fixtures_dir, "sample_statement_bank_b.pdf")
    
    with open(pdf_path, "rb") as f:
        parsed = parser.parse(f.read())
        
    assert isinstance(parsed, ParsedStatement)
    assert parsed.issuing_bank == "PdfBank"
    assert parsed.purchase_balance == 100000.0
    assert parsed.purchase_apr == 0.28
    assert parsed.minimum_payment == 5000.0
    assert parsed.due_date == date(2026, 8, 25)
    assert len(parsed.transactions) == 3
    assert parsed.transactions[1].amount == 25000.0

def test_upload_statement_endpoint(client: TestClient, session: Session):
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    pdf_path = os.path.join(fixtures_dir, "sample_statement_bank_b.pdf")
    
    with open(pdf_path, "rb") as f:
        response = client.post(
            "/statements/upload",
            data={"issuing_bank": "pdfbank"},
            files={"file": ("sample_statement_bank_b.pdf", f, "application/pdf")}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Success"
    assert data["transactions_count"] == 3
    
    statement_id = data["statement_id"]
    
    # Verify in DB
    db_statement = session.get(Statement, statement_id)
    assert db_statement is not None
    assert db_statement.purchase_balance == 100000.0
    assert db_statement.purchase_apr == 0.28
    
    # Verify transactions in DB
    db_txs = session.query(Transaction).filter(Transaction.statement_id == statement_id).all()
    assert len(db_txs) == 3
