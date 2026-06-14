from pydantic import BaseModel, EmailStr
from typing import Optional


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    business_type: str = "freelancer"
    monthly_income_range: str = "0-100000"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    business_type: str
    monthly_income_range: str
    subscription_plan: str
    onboarding_completed: bool
    pidgin_mode: bool
    created_at: str


class TransactionCreate(BaseModel):
    amount: float
    type: str
    category: str
    description: str
    date: Optional[str] = None
    bank_account_id: Optional[str] = None


class TransactionResponse(BaseModel):
    id: str
    user_id: str
    amount: float
    type: str
    category: str
    description: str
    date: str
    bank_account_id: Optional[str]
    is_recurring: bool
    ai_categorized: bool
    flagged: bool
    created_at: str


class BankAccountCreate(BaseModel):
    bank_name: str
    account_number: str
    account_name: str


class BankAccountResponse(BaseModel):
    id: str
    user_id: str
    bank_name: str
    account_number: str
    account_name: str
    balance: float
    linked: bool
    last_synced: Optional[str]
    created_at: str


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    plan: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class PaymentInitRequest(BaseModel):
    plan: str
    callback_url: Optional[str] = None


class MonoLinkRequest(BaseModel):
    institution_id: Optional[str] = None


class TeamMemberInvite(BaseModel):
    email: EmailStr
    role: str = "viewer"
