"""
Estimates future available funds based on historical profiles and predicted bills.
"""
from datetime import date
from sqlmodel import Session, select
from app.models import FinancialBehaviorProfile, Statement, Transaction
from app.agents.spending_insights import forecast_upcoming_bills
from typing import Dict, List
import datetime

def _get_last_salary_amount(user_id: int, session: Session) -> float:
    """
    Attempts to find the most recent salary-like transaction amount.
    Defaults to 5000.0 if none found.
    """
    statements = session.exec(
        select(Statement).where(Statement.user_id == user_id)
    ).all()
    
    if not statements:
        return 5000.0
        
    statement_ids = [s.id for s in statements]
    
    # We look for large credits or explicit salary keywords (matching the behavioral agent heuristic)
    salary_keywords = {"salary", "payroll", "direct deposit", "wage"}
    
    transactions = session.exec(
        select(Transaction)
        .where(Transaction.statement_id.in_(statement_ids))
        .order_by(Transaction.date.desc())
    ).all()
    
    for tx in transactions:
        desc_lower = tx.description.lower()
        if any(kw in desc_lower for kw in salary_keywords):
            # Assume positive amount for income
            return abs(tx.amount)
            
    # Fallback to a large credit > 1000
    for tx in transactions:
        if tx.amount > 1000:
            return tx.amount
            
    return 5000.0


def forecast_available_funds(user_id: int, candidate_dates: List[date], session: Session) -> Dict[date, float]:
    """
    Estimates funds likely available for the given candidate dates.
    
    Estimation Formula (Decision Support Only):
    - Starts with an initial assumed baseline of 0.0 funds at `start_date` (today).
    - For a candidate date `D`:
      1. Adds `last_known_salary` for every occurrence of `salary_cycle_day` between today and `D`.
      2. Subtracts the sum of all forecasted recurring bills due between today and `D`.
      3. Subtracts a prorated amount of the user's `avg_discretionary_spend` (daily spend * days elapsed)
         to account for non-committed "lifestyle" drag.
         
    Disclaimer: This is explicitly an estimate and not a guarantee. It is meant to provide 
    decision support for the Deposit Recommendation Agent, not autonomous execution.
    """
    if not candidate_dates:
        return {}
        
    profile = session.exec(
        select(FinancialBehaviorProfile).where(FinancialBehaviorProfile.user_id == user_id)
    ).first()
    
    # If no profile, we can't forecast properly. We'll return 0 for everything.
    if not profile:
        return {d: 0.0 for d in candidate_dates}
        
    start_date = datetime.date.today()
    max_date = max(candidate_dates)
    
    if max_date < start_date:
        # Cannot forecast in the past
        return {d: 0.0 for d in candidate_dates}

    salary_amount = _get_last_salary_amount(user_id, session)
    
    # Fetch all bills once up to the furthest date to avoid N+1 queries
    all_bills = forecast_upcoming_bills(user_id, start_date, max_date, session)
    
    forecasts = {}
    
    for c_date in candidate_dates:
        # If the candidate date is in the past, just yield 0
        if c_date < start_date:
            forecasts[c_date] = 0.0
            continue
            
        days_elapsed = (c_date - start_date).days
        
        # 1. Calculate Salary Additions
        salary_additions = 0.0
        # Iterate over months between start_date and c_date
        current = start_date
        while current <= c_date:
            # Did the salary day happen this month in the range?
            try:
                cycle_date = date(current.year, current.month, profile.salary_cycle_day)
                if start_date <= cycle_date <= c_date:
                    salary_additions += salary_amount
            except ValueError:
                # E.g. cycle day is 31, but month is Feb. 
                pass
                
            # Move to next month
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)
                
        # 2. Calculate Bill Subtractions
        bill_subtractions = 0.0
        for bill in all_bills:
            if start_date <= bill["date"] <= c_date:
                bill_subtractions += bill["amount"]
                
        # 3. Calculate Discretionary Drag
        # avg_discretionary_spend is a monthly figure. Daily is approx / 30.
        daily_drag = profile.avg_discretionary_spend / 30.0
        discretionary_drag = daily_drag * days_elapsed
        
        # Assemble Final Estimate
        estimated_funds = salary_additions - bill_subtractions - discretionary_drag
        forecasts[c_date] = round(estimated_funds, 2)
        
    return forecasts
