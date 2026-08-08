from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select
from app.db import get_session
from app.models import Statement, Transaction, User, FinancialBehaviorProfile
from app.agents.statement_parsing import ParserRegistry
from app.agents.statement_explainability import explain_statement
from app.agents.behavioral_profiling import update_profile
from app.agents.cash_flow_forecast import forecast_available_funds
from app.agents.deposit_recommendation import recommend_deposit_schedule
from app.agents.conversational_query import answer_question
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

class RiskToleranceUpdate(BaseModel):
    user_id: int
    risk_tolerance: str

class ChatRequest(BaseModel):
    question: str

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

@app.post("/profile/refresh/{user_id}")
async def refresh_profile(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    profile = update_profile(user_id, session)
    return profile

@app.get("/profile/{user_id}")
async def get_profile(user_id: int, session: Session = Depends(get_session)):
    profile = session.exec(select(FinancialBehaviorProfile).where(FinancialBehaviorProfile.user_id == user_id)).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@app.patch("/profile")
async def update_risk_tolerance(update_data: RiskToleranceUpdate, session: Session = Depends(get_session)):
    profile = session.exec(select(FinancialBehaviorProfile).where(FinancialBehaviorProfile.user_id == update_data.user_id)).first()
    if not profile:
        # Create a stub profile to hold the risk tolerance if it doesn't exist
        profile = FinancialBehaviorProfile(
            user_id=update_data.user_id,
            salary_cycle_day=1,
            avg_discretionary_spend=0.0,
            repayment_adherence_score=0.5,
            risk_tolerance=update_data.risk_tolerance
        )
        session.add(profile)
    else:
        profile.risk_tolerance = update_data.risk_tolerance
        session.add(profile)
        
    session.commit()
    session.refresh(profile)
    return profile

from datetime import date
from typing import List
from fastapi import Query

@app.get("/cashflow/forecast/{user_id}")
async def get_cashflow_forecast(
    user_id: int, 
    candidate_dates: List[date] = Query(...), 
    session: Session = Depends(get_session)
):
    try:
        forecast = forecast_available_funds(user_id, candidate_dates, session)
        return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from datetime import timedelta
import json

@app.post("/recommendations/{statement_id}")
async def generate_recommendation(
    statement_id: int, 
    session: Session = Depends(get_session)
):
    statement = session.get(Statement, statement_id)
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")
        
    user_id = statement.user_id
    
    # Generate candidate dates between statement_date and due_date
    candidate_dates = []
    current = statement.statement_date
    while current <= statement.due_date:
        candidate_dates.append(current)
        current += timedelta(days=1)
        
    forecast = forecast_available_funds(user_id, candidate_dates, session, start_date=statement.statement_date)
    
    rec = recommend_deposit_schedule(statement, forecast, session)
    
    schedule = json.loads(rec.schedule_json)
    schedule_strs = [f"LKR {amt:,.2f} on {d}" for d, amt in schedule.items()]
    schedule_summary = " and ".join(schedule_strs)
    
    if rec.projected_interest < rec.baseline_interest:
        reduction_pct = ((rec.baseline_interest - rec.projected_interest) / rec.baseline_interest) * 100
        savings_summary = (
            f"Depositing {schedule_summary} is projected to reduce this cycle's "
            f"interest by {reduction_pct:.0f}%, from LKR {rec.baseline_interest:,.2f} to LKR {rec.projected_interest:,.2f}"
        )
    else:
        savings_summary = "No interest savings found over baseline."
        
    return {
        "recommendation_id": rec.id,
        "schedule": schedule,
        "projected_interest": rec.projected_interest,
        "baseline_interest": rec.baseline_interest,
        "savings_summary": savings_summary
    }

@app.post("/chat/{user_id}")
async def chat_endpoint(
    user_id: int, 
    request: ChatRequest, 
    session: Session = Depends(get_session),
    llm_client: LLMClient = Depends(get_llm_client)
):
    answer = answer_question(user_id, request.question, session, llm_client)
    return {"answer": answer}

@app.get("/dashboard/{user_id}")
async def get_dashboard_data(
    user_id: int, 
    session: Session = Depends(get_session)
):
    # Aggregator endpoint for the frontend
    statement = session.exec(
        select(Statement).where(Statement.user_id == user_id).order_by(Statement.id.desc())
    ).first()
    
    if not statement:
        raise HTTPException(status_code=404, detail="No statements found")
        
    profile = session.exec(select(FinancialBehaviorProfile).where(FinancialBehaviorProfile.user_id == user_id)).first()
    
    # We won't re-run explain_statement dynamically here (it takes LLM time). 
    # In a real app we'd persist the explanation. For now, we'll return a stub or we could call it if FakeLLM.
    # Let's return a static list of explanations to simulate what the frontend would get from DB.
    explanations = [
        {"line_item_name": "Purchase Balance", "plain_language_explanation": "This is the total amount you owe from regular purchases."},
        {"line_item_name": "Minimum Payment", "plain_language_explanation": "This is the absolute least you must pay to avoid penalties."}
    ]
    
    recommendation = session.exec(
        select(DepositRecommendation).where(DepositRecommendation.statement_id == statement.id).order_by(DepositRecommendation.id.desc())
    ).first()
    
    rec_data = None
    if recommendation:
        schedule = json.loads(recommendation.schedule_json)
        schedule_strs = [f"LKR {amt:,.2f} on {d}" for d, amt in schedule.items()]
        schedule_summary = " and ".join(schedule_strs)
        if recommendation.projected_interest < recommendation.baseline_interest:
            reduction_pct = ((recommendation.baseline_interest - recommendation.projected_interest) / recommendation.baseline_interest) * 100
            savings_summary = (
                f"Depositing {schedule_summary} is projected to reduce this cycle's "
                f"interest by {reduction_pct:.0f}%, from LKR {recommendation.baseline_interest:,.2f} to LKR {recommendation.projected_interest:,.2f}"
            )
        else:
            savings_summary = "No interest savings found over baseline."
            
        rec_data = {
            "schedule": schedule,
            "projected_interest": recommendation.projected_interest,
            "baseline_interest": recommendation.baseline_interest,
            "savings_summary": savings_summary
        }
        
    # Low-value subscriptions stub (Day 6 feature)
    low_value_subs = [
        {"name": "Streaming Service A", "amount": 1500.0, "reason": "You haven't used this in 3 months."},
        {"name": "Gym Membership", "amount": 5000.0, "reason": "Flagged as potentially unused based on average behavior."}
    ]

    return {
        "statement_summary": {
            "balance": statement.purchase_balance,
            "due_date": statement.due_date,
            "minimum_payment": statement.minimum_payment
        },
        "explanations": explanations,
        "recommendation": rec_data,
        "low_value_subscriptions": low_value_subs
    }
