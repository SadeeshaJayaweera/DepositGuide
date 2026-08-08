from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from app.db import get_session
from app.models import Statement, Transaction, User
from app.agents.statement_parsing import ParserRegistry
from app.agents.statement_explainability import explain_statement
from app.agents.interest_engine import compute_interest_breakdown
from app.llm.client import get_llm_client, LLMClient

app = FastAPI(title="DepositGuide API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/statements/upload")
async def upload_statement(
    file: UploadFile = File(...),
    issuing_bank: str = Form(...),
    session: Session = Depends(get_session)
):
    try:
        parser = ParserRegistry.get_parser(issuing_bank)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    file_bytes = await file.read()
    try:
        parsed = parser.parse(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse statement: {str(e)}")

    # Get or create a default user for testing
    user = session.exec(select(User)).first()
    if not user:
        user = User(email="test@example.com")
        session.add(user)
        session.commit()
        session.refresh(user)

    # Save statement
    statement = Statement(
        user_id=user.id,
        issuing_bank=parsed.issuing_bank,
        statement_date=parsed.statement_date,
        due_date=parsed.due_date,
        minimum_payment=parsed.minimum_payment,
        purchase_apr=parsed.purchase_apr,
        cash_advance_apr=parsed.cash_advance_apr,
        purchase_balance=parsed.purchase_balance,
        cash_advance_balance=parsed.cash_advance_balance,
        raw_source_filename=file.filename or "unknown"
    )
    session.add(statement)
    session.commit()
    session.refresh(statement)

    # Save transactions
    for tx in parsed.transactions:
        db_tx = Transaction(
            statement_id=statement.id,
            date=tx.date,
            description=tx.description,
            amount=tx.amount,
            category=tx.raw_category_hint or "Uncategorized",
        )
        session.add(db_tx)
    session.commit()

    return {"message": "Success", "statement_id": statement.id, "transactions_count": len(parsed.transactions)}

@app.get("/statements/{statement_id}/explain")
async def explain_statement_endpoint(
    statement_id: int,
    language: str = "en",
    session: Session = Depends(get_session),
    llm_client: LLMClient = Depends(get_llm_client)
):
    statement = session.get(Statement, statement_id)
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")

    transactions = session.exec(select(Transaction).where(Transaction.statement_id == statement_id)).all()
    
    interest_breakdown = compute_interest_breakdown(statement)
    
    try:
        explanation = explain_statement(
            statement=statement,
            transactions=transactions,
            interest_breakdown=interest_breakdown,
            llm_client=llm_client,
            language=language
        )
        return explanation.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
