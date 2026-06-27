from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class Category(str, Enum):
    FOOD = "Food"
    TRAVEL = "Travel"
    SHOPPING = "Shopping"
    BILLS = "Bills"
    EMI = "EMI"
    SUBSCRIPTIONS = "Subscriptions"
    SALARY = "Salary"
    RENT = "Rent"
    INVESTMENTS = "Investments"
    OTHER = "Other"

class TransactionType(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"

class CategorySource(str, Enum):
    RULE = "rule"
    LLM = "llm"
    USER = "user"

class Transaction(BaseModel):
    id: str
    sessionId: str
    date: str  # ISO date YYYY-MM-DD
    rawDescription: str
    cleanDescription: str
    merchant: Optional[str] = None
    amount: float  # negative = expense, positive = income
    type: TransactionType
    category: Category
    categoryConfidence: float = Field(default=1.0, ge=0.0, le=1.0)
    categorySource: CategorySource = CategorySource.RULE
    isRecurring: bool = False
    recurringGroupId: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class RecurringType(str, Enum):
    SUBSCRIPTION = "subscription"
    EMI = "emi"
    RENT = "rent"
    SIP = "sip"
    INSURANCE = "insurance"
    OTHER = "other"

class RecurringFrequency(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class RecurringItem(BaseModel):
    id: str
    merchant: str
    category: Category
    recurringType: RecurringType
    amount: float
    frequency: RecurringFrequency
    occurrences: int
    transactionIds: List[str]
    monthlyEquivalent: float

    class Config:
        from_attributes = True

class CategoryAggregate(BaseModel):
    category: Category
    amount: float
    percentage: float

class AnalysisSummary(BaseModel):
    sessionId: str
    periodStart: str
    periodEnd: str
    totalIncome: float
    totalSpend: float
    savings: float
    savingsRate: float
    transactionCount: int
    topCategories: List[CategoryAggregate]
    biggestTransaction: Optional[Transaction] = None
    recurringMonthlyTotal: float

    class Config:
        from_attributes = True
