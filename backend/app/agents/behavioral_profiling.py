"""
Analyzes historical transactions to model user discretionary spend and risk tolerance.
"""
from datetime import datetime
from collections import defaultdict
from sqlmodel import Session, select
from app.models import (
    FinancialBehaviorProfile, 
    Statement, 
    Transaction, 
    DepositRecommendation
)

NON_ESSENTIAL_CATEGORIES = {"Dining", "Entertainment", "Shopping", "Travel", "Hobbies"}
SALARY_KEYWORDS = {"salary", "payroll", "direct deposit", "wage"}

def _infer_salary_cycle_day(transactions: list[Transaction]) -> int:
    """
    Heuristic to infer the salary cycle day:
    1. Looks for transactions with descriptions matching common salary keywords.
    2. If no keywords match, falls back to the most regular high-value recurring positive credit.
    3. Finds the most common day of the month for these credits.
    4. Defaults to 1 if no transactions exist.
    """
    if not transactions:
        return 1

    salary_txs = []
    
    # 1. Look for explicit keywords
    for tx in transactions:
        desc_lower = tx.description.lower()
        if any(keyword in desc_lower for keyword in SALARY_KEYWORDS):
            salary_txs.append(tx)
            
    # 2. Fallback to large credits (assuming amount > 0 means income in this simplified model)
    if not salary_txs:
        # Assuming credits are positive and relatively large (e.g., > 1000)
        large_credits = [tx for tx in transactions if tx.amount > 1000]
        if large_credits:
            salary_txs = large_credits

    if not salary_txs:
        return 1
        
    day_counts = defaultdict(int)
    for tx in salary_txs:
        day_counts[tx.date.day] += 1
        
    # Find the most frequent day
    best_day = max(day_counts.items(), key=lambda x: x[1])[0]
    return best_day

def _compute_avg_discretionary_spend(session: Session, user_id: int) -> float:
    """
    Computes the average of transactions categorized as non-essential over the last 3 statement cycles.
    """
    # Fetch last 3 statements ordered by date descending
    statements = session.exec(
        select(Statement)
        .where(Statement.user_id == user_id)
        .order_by(Statement.statement_date.desc())
        .limit(3)
    ).all()
    
    if not statements:
        return 0.0

    total_spend = 0.0
    statement_ids = [s.id for s in statements]
    
    transactions = session.exec(
        select(Transaction)
        .where(Transaction.statement_id.in_(statement_ids))
    ).all()
    
    discretionary_txs = [
        tx for tx in transactions 
        if tx.category in NON_ESSENTIAL_CATEGORIES
    ]
    
    # Sum of discretionary spend (assuming amount is positive for debits in CC statements,
    # or just use abs(amount) to be safe)
    for tx in discretionary_txs:
        total_spend += abs(tx.amount)
        
    return total_spend / len(statements)

def _compute_repayment_adherence_score(session: Session, user_id: int) -> float:
    """
    Computes score based on how consistently past DepositRecommendations were followed.
    Defaults to 0.5 if no history exists yet. This will improve over time.
    """
    recommendations = session.exec(
        select(DepositRecommendation).where(DepositRecommendation.user_id == user_id)
    ).all()
    
    if not recommendations:
        # Default as per requirement
        return 0.5
        
    # TODO: In the future, join with actual payment transactions to compute a real ratio.
    # For now, return a placeholder default that could be adjusted by actual future agent logic.
    return 0.5

def update_profile(user_id: int, session: Session) -> FinancialBehaviorProfile:
    """
    Updates or creates the FinancialBehaviorProfile for the user.
    """
    # Fetch all user transactions to infer salary day
    statements = session.exec(select(Statement).where(Statement.user_id == user_id)).all()
    statement_ids = [s.id for s in statements]
    
    if statement_ids:
        transactions = session.exec(
            select(Transaction).where(Transaction.statement_id.in_(statement_ids))
        ).all()
    else:
        transactions = []
        
    salary_day = _infer_salary_cycle_day(transactions)
    avg_spend = _compute_avg_discretionary_spend(session, user_id)
    adherence_score = _compute_repayment_adherence_score(session, user_id)
    
    profile = session.exec(
        select(FinancialBehaviorProfile).where(FinancialBehaviorProfile.user_id == user_id)
    ).first()
    
    if not profile:
        profile = FinancialBehaviorProfile(
            user_id=user_id,
            salary_cycle_day=salary_day,
            avg_discretionary_spend=avg_spend,
            repayment_adherence_score=adherence_score,
            risk_tolerance="moderate"
        )
        session.add(profile)
    else:
        profile.salary_cycle_day = salary_day
        profile.avg_discretionary_spend = avg_spend
        profile.repayment_adherence_score = adherence_score
        profile.updated_at = datetime.utcnow()
        # risk_tolerance is explicitly preserved
        session.add(profile)
        
    session.commit()
    session.refresh(profile)
    return profile
