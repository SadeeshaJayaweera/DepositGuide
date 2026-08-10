from typing import List, Dict, Any
from pydantic import BaseModel
from app.models import Statement, Transaction
from app.llm.client import LLMClient
import json

class LineItemExplanation(BaseModel):
    line_item_name: str
    plain_language_explanation: str

class ExplainedStatement(BaseModel):
    explanations: List[LineItemExplanation]

def explain_statement(
    statement: Statement, 
    transactions: List[Transaction], 
    interest_breakdown: Dict[str, Any], 
    llm_client: LLMClient, 
    language: str = "en"
) -> ExplainedStatement:
    
    system_prompt = f"""You are a strict, highly accurate financial advisor. Your goal is to explain the user's banking statement to them in plain language, in the requested language ({language}).
CRITICAL RULES:
1. You MUST use the exact numbers provided in the user's prompt. 
2. Do NOT invent, guess, or round any numbers (balances, APRs, interest figures). Use exactly what is given.
3. You must output a JSON object containing a list of 'explanations', where each explanation has a 'line_item_name' and a 'plain_language_explanation'. 
Example output structure:
{{
    "explanations": [
        {{"line_item_name": "Purchase Balance", "plain_language_explanation": "..."}}
    ]
}}
"""

    user_prompt = f"""Please explain my statement:
Issuing Bank: {statement.issuing_bank}
Statement Date: {statement.statement_date}
Due Date: {statement.due_date}
Minimum Payment: {statement.minimum_payment}
Purchase APR: {statement.purchase_apr}
Cash Advance APR: {statement.cash_advance_apr}
Purchase Balance: {statement.purchase_balance}
Cash Advance Balance: {statement.cash_advance_balance}

Interest Breakdown:
Projected Interest: {interest_breakdown.get('projected_interest')}
Baseline Interest: {interest_breakdown.get('baseline_interest')}

Explain the balances, APRs, and what the projected interest means in simple terms.
"""

    response_text = llm_client.generate(system_prompt=system_prompt, user_prompt=user_prompt, response_mime_type="application/json")
    
    # Simple cleanup if the LLM wrapped it in markdown code blocks
    if response_text.startswith("```json"):
        response_text = response_text[7:-3].strip()
    elif response_text.startswith("```"):
        response_text = response_text[3:-3].strip()
        
    data = json.loads(response_text)
    return ExplainedStatement(**data)
