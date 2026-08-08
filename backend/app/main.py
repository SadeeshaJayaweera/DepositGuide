from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlmodel import Session, select
from datetime import date, timedelta
import json
import os
from dotenv import load_dotenv

from google.oauth2 import id_token
from google.auth.transport import requests

load_dotenv()

from app.db import get_session
from app.models import Statement, Transaction, User, FinancialBehaviorProfile, DepositRecommendation
from app.agents.statement_parsing import ParserRegistry
from app.agents.statement_explainability import explain_statement
from app.agents.behavioral_profiling import update_profile
from app.agents.cash_flow_forecast import forecast_available_funds
from app.agents.deposit_recommendation import recommend_deposit_schedule
from app.agents.conversational_query import answer_question
from app.agents.interest_engine import compute_interest_breakdown
from app.llm.client import get_llm_client, LLMClient
from app.auth import get_password_hash, verify_password, create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES

app = FastAPI(title="DepositGuide API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class GoogleAuthRequest(BaseModel):
    token: str

class RiskToleranceUpdate(BaseModel):
    risk_tolerance: str

class ChatRequest(BaseModel):
    question: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == user_data.email)).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(email=user_data.email, hashed_password=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/google", response_model=Token)
async def google_auth(request: GoogleAuthRequest, session: Session = Depends(get_session)):
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="Google Client ID not configured")
        
    try:
        # Verify the Google ID token
        idinfo = id_token.verify_oauth2_token(request.token, requests.Request(), client_id)
        email = idinfo.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Google account has no email")
            
        # Look up or create user
        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            # Create user with an unusable password hash
            user = User(email=email, hashed_password="google_oauth_no_password")
            session.add(user)
            session.commit()
            session.refresh(user)
            
        # Issue our own JWT
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")

@app.post("/statements/upload")
async def upload_statement(
    file: UploadFile = File(...),
    issuing_bank: str = Form(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
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

    # Save statement
    statement = Statement(
        user_id=current_user.id,
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
    llm_client: LLMClient = Depends(get_llm_client),
    current_user: User = Depends(get_current_user)
):
    statement = session.get(Statement, statement_id)
    if not statement or statement.user_id != current_user.id:
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

@app.post("/profile/refresh")
async def refresh_profile(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    profile = update_profile(current_user.id, session)
    return profile

@app.get("/profile")
async def get_profile(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    profile = session.exec(select(FinancialBehaviorProfile).where(FinancialBehaviorProfile.user_id == current_user.id)).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@app.patch("/profile")
async def update_risk_tolerance(
    update_data: RiskToleranceUpdate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    profile = session.exec(select(FinancialBehaviorProfile).where(FinancialBehaviorProfile.user_id == current_user.id)).first()
    if not profile:
        profile = FinancialBehaviorProfile(
            user_id=current_user.id,
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

@app.post("/recommendations/{statement_id}")
async def generate_recommendation(
    statement_id: int, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    statement = session.get(Statement, statement_id)
    if not statement or statement.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Statement not found")
        
    candidate_dates = []
    current = statement.statement_date
    while current <= statement.due_date:
        candidate_dates.append(current)
        current += timedelta(days=1)
        
    forecast = forecast_available_funds(current_user.id, candidate_dates, session, start_date=statement.statement_date)
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

@app.post("/chat")
async def chat_endpoint(
    request: ChatRequest, 
    session: Session = Depends(get_session),
    llm_client: LLMClient = Depends(get_llm_client),
    current_user: User = Depends(get_current_user)
):
    answer = answer_question(current_user.id, request.question, session, llm_client)
    return {"answer": answer}

@app.get("/dashboard")
async def get_dashboard_data(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    statement = session.exec(
        select(Statement).where(Statement.user_id == current_user.id).order_by(Statement.id.desc())
    ).first()
    
    if not statement:
        raise HTTPException(status_code=404, detail="No statements found")
        
    profile = session.exec(select(FinancialBehaviorProfile).where(FinancialBehaviorProfile.user_id == current_user.id)).first()
    
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
