"""
Answers user queries grounded in their specific financial data.
"""
from sqlmodel import Session, select
from app.models import Statement, FinancialBehaviorProfile, DepositRecommendation
from app.llm.client import LLMClient
from app.agents.memory_agent import extract_and_save_facts, retrieve_relevant_facts
import json

def answer_question(user_id: int, question: str, session: Session, llm_client: LLMClient) -> str:
    """
    Assembles a grounded context object, including retrieved user facts, and calls the LLM to answer the question.
    """
    # 0. Memory Extraction and Retrieval
    extract_and_save_facts(user_id, question, session, llm_client)
    retrieved_facts = retrieve_relevant_facts(user_id, question, session, llm_client)
    # 1. Fetch Latest Statement
    statement = session.exec(
        select(Statement).where(Statement.user_id == user_id).order_by(Statement.id.desc())
    ).first()
    
    if not statement:
        return "I couldn't find any recent statements for your account. Please upload one first."
        
    # 2. Fetch Financial Behavior Profile
    profile = session.exec(
        select(FinancialBehaviorProfile).where(FinancialBehaviorProfile.user_id == user_id)
    ).first()
    
    # 3. Fetch Latest Deposit Recommendation
    recommendation = session.exec(
        select(DepositRecommendation).where(DepositRecommendation.statement_id == statement.id).order_by(DepositRecommendation.id.desc())
    ).first()
    
    # Assemble Context
    context = {
        "statement": {
            "issuing_bank": statement.issuing_bank,
            "statement_date": statement.statement_date.isoformat(),
            "due_date": statement.due_date.isoformat(),
            "minimum_payment": statement.minimum_payment,
            "purchase_apr": statement.purchase_apr,
            "purchase_balance": statement.purchase_balance,
        },
        "profile": {
            "salary_cycle_day": profile.salary_cycle_day if profile else "Unknown",
            "risk_tolerance": profile.risk_tolerance if profile else "Unknown"
        },
        "retrieved_user_facts": retrieved_facts,
        "recommendation": None
    }
    
    if recommendation:
        context["recommendation"] = {
            "schedule": json.loads(recommendation.schedule_json),
            "projected_interest": recommendation.projected_interest,
            "baseline_interest": recommendation.baseline_interest
        }
        
    context_str = json.dumps(context, indent=2)
    
    system_prompt = f"""You are DepositGuide, a helpful financial assistant.
You have been provided with the user's highly sensitive financial context below.
You must answer the user's question ONLY using the provided context. 
If the question falls outside of this context (e.g. asking for checking account balances, weather, or unprovided data), you MUST politely refuse and state that you do not have enough information.
Do not invent or guess any numbers.

CONTEXT:
{context_str}
"""

    return llm_client.generate(system_prompt=system_prompt, user_prompt=question)
