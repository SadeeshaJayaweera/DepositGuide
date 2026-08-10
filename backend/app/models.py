from typing import Optional
from datetime import datetime, date
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Statement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    issuing_bank: str
    statement_date: date
    due_date: date
    minimum_payment: float
    purchase_apr: float
    cash_advance_apr: float
    purchase_balance: float
    cash_advance_balance: float
    raw_source_filename: str

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    statement_id: int = Field(foreign_key="statement.id")
    date: date
    description: str
    amount: float
    category: str
    is_recurring: bool = Field(default=False)

class FinancialBehaviorProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    salary_cycle_day: int
    avg_discretionary_spend: float
    repayment_adherence_score: float
    risk_tolerance: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class DepositRecommendation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    statement_id: int = Field(foreign_key="statement.id")
    recommended_at: datetime = Field(default_factory=datetime.utcnow)
    schedule_json: str
    projected_interest: float
    baseline_interest: float

class UserMemory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    fact: str
    embedding_json: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
