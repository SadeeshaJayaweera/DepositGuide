"""
Calculates projected and baseline interest for deposits.
"""
from typing import Dict, Any
from datetime import date, timedelta
from app.models import Statement

def compute_interest_for_schedule(statement: Statement, schedule: Dict[date, float]) -> float:
    """
    Computes total accrued interest over the billing cycle for a given schedule.
    """
    dpr = statement.purchase_apr / 365.0
    balance = statement.purchase_balance
    total_interest = 0.0
    
    current_date = statement.statement_date
    end_date = statement.due_date
    
    while current_date <= end_date:
        # Accumulate daily interest on the starting balance
        daily_interest = balance * dpr
        total_interest += daily_interest
        
        # Process deposits for the day (takes effect for next day's interest)
        if current_date in schedule:
            balance = max(0.0, balance - schedule[current_date])
            
        current_date += timedelta(days=1)
        
    return total_interest

def compute_interest_breakdown(statement: Statement) -> Dict[str, Any]:
    """
    Returns baseline interest breakdown (assuming min payment on due date).
    """
    # Baseline schedule: only minimum payment on the due date
    baseline_schedule = {
        statement.due_date: statement.minimum_payment
    }
    
    baseline_interest = compute_interest_for_schedule(statement, baseline_schedule)
    
    return {
        "projected_interest": baseline_interest, # Will be replaced by optimal
        "baseline_interest": baseline_interest,
        "savings_potential": 0.0
    }
