"""
Optimizes deposit schedules to minimize interest subject to cash-flow constraints.
"""
import json
from datetime import date, timedelta
from typing import Dict, List
from sqlmodel import Session
from app.models import Statement, DepositRecommendation
from app.agents.interest_engine import compute_interest_for_schedule

def recommend_deposit_schedule(
    statement: Statement, 
    cash_flow_forecast: Dict[date, float], 
    session: Session
) -> DepositRecommendation:
    """
    Evaluates candidate schedules and selects the feasible one minimizing total interest.
    """
    min_payment = statement.minimum_payment
    balance = statement.purchase_balance
    due_date = statement.due_date
    start_date = statement.statement_date
    
    # 1. Baseline: Minimum payment on the due date
    baseline_schedule = {due_date: min_payment}
    baseline_interest = compute_interest_for_schedule(statement, baseline_schedule)
    
    best_schedule = baseline_schedule
    best_interest = baseline_interest
    
    # Pre-compute a list of days between start and due (excluding due)
    early_days = []
    current = start_date
    while current < due_date:
        early_days.append(current)
        current += timedelta(days=1)
        
    candidates: List[Dict[date, float]] = []
    
    # Candidate 2: Full Payoff (find the earliest day where we can pay full balance)
    for d in early_days:
        if cash_flow_forecast.get(d, 0.0) >= balance:
            candidates.append({d: balance})
            # Once we find the earliest full payoff, we don't need later ones
            break
            
    # Candidate 3: Grid of Two-Installment Partial Schedules
    # We'll try paying 25%, 50%, and 75% of the balance on every early day
    fractions = [0.25, 0.50, 0.75]
    
    for d in early_days:
        forecast_on_d = cash_flow_forecast.get(d, 0.0)
        for frac in fractions:
            partial_amount = round(balance * frac, 2)
            # Must be feasible under cash flow constraint
            if forecast_on_d >= partial_amount:
                # We also must ensure total payment >= min_payment
                # We'll pay the remainder on the due date, up to the max we have, 
                # but for simplicity, we assume we just pay min_payment minus partial_amount
                # if min_payment wasn't met, or just 0 if it was.
                # However, to be a valid schedule, total paid >= min_payment.
                # Let's assume we pay the max remainder we need:
                # If we want to pay it off completely, remainder = balance - partial_amount
                # But we might not have enough cash on due_date to pay the rest of the balance.
                # Let's say remainder = max(min_payment - partial_amount, 0)
                # But depositing more early is strictly better. So let's test a schedule where
                # we deposit the partial amount early, and exactly whatever is needed to hit Min Payment on due date.
                
                remainder_needed = max(min_payment - partial_amount, 0.0)
                
                # Check if remainder_needed is feasible on due_date
                forecast_on_due = cash_flow_forecast.get(due_date, 0.0)
                # Note: The cash flow forecast represents cumulative available funds, 
                # but if we spent 'partial_amount', we actually only have forecast_on_due - partial_amount left.
                # This is a simplification, but assuming cash forecast > partial_amount + remainder_needed
                if forecast_on_due - partial_amount >= remainder_needed:
                    cand = {d: partial_amount}
                    if remainder_needed > 0:
                        cand[due_date] = remainder_needed
                    candidates.append(cand)
                    
                # Let's also test a schedule where we pay partial early, and the FULL remainder on due date
                # to clear the balance, if feasible.
                full_remainder = balance - partial_amount
                if forecast_on_due - partial_amount >= full_remainder:
                    cand_full = {d: partial_amount, due_date: full_remainder}
                    candidates.append(cand_full)
                    
    # Evaluate all candidates
    for cand in candidates:
        interest = compute_interest_for_schedule(statement, cand)
        if interest < best_interest:
            best_interest = interest
            best_schedule = cand
            
    # Serialize schedule keys to strings for JSON
    str_schedule = {d.isoformat(): amt for d, amt in best_schedule.items()}
    
    rec = DepositRecommendation(
        user_id=statement.user_id,
        statement_id=statement.id,
        schedule_json=json.dumps(str_schedule),
        projected_interest=best_interest,
        baseline_interest=baseline_interest
    )
    
    session.add(rec)
    session.commit()
    session.refresh(rec)
    
    return rec
