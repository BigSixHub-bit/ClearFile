from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, File, UploadFile, Response, Query
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import logging
import uuid
import bcrypt
import jwt
import secrets
import requests
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional
from pathlib import Path

# Emergent Integrations for AI
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_ALGORITHM = "HS256"

def get_jwt_secret() -> str:
    return os.environ["JWT_SECRET"]

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        "type": "access"
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "refresh"
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

# Object Storage for Receipt Uploads
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = "nairatrack"
storage_key = None

def init_storage():
    global storage_key
    if storage_key:
        return storage_key
    try:
        resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=30)
        resp.raise_for_status()
        storage_key = resp.json()["storage_key"]
        return storage_key
    except Exception as e:
        logger.error(f"Storage init failed: {e}")
        return None

def put_object(path: str, data: bytes, content_type: str) -> dict:
    key = init_storage()
    if not key:
        raise Exception("Storage not initialized")
    resp = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data, timeout=120
    )
    resp.raise_for_status()
    return resp.json()

def get_object(path: str) -> tuple:
    key = init_storage()
    if not key:
        raise Exception("Storage not initialized")
    resp = requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key}, timeout=60
    )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")

# Create the main app
app = FastAPI(title="NairaTrack API", description="Nigerian Tax & Expense Management")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ========================
# PYDANTIC MODELS
# ========================

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    business_type: str = "freelancer"  # freelancer, sme, company
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
    type: str  # income or expense
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
    plan: str  # starter, growth, business

# Nigerian Tax Rates
PITA_RATES = [
    (300000, 0.07),
    (300000, 0.11),
    (500000, 0.15),
    (500000, 0.19),
    (1600000, 0.21),
    (float('inf'), 0.24)
]

CITA_RATE_SMALL = 0.20  # < 25M turnover
CITA_RATE_LARGE = 0.30  # >= 25M turnover
VAT_RATE = 0.075
WHT_RATES = {
    "dividends": 0.10,
    "interest": 0.10,
    "rent": 0.10,
    "royalties": 0.10,
    "professional_fees": 0.10,
    "contracts": 0.05
}

EXPENSE_CATEGORIES = [
    "Salaries", "Rent", "Utilities", "Transport", "Equipment",
    "Marketing", "Professional Fees", "Subscriptions", "Miscellaneous"
]

INCOME_CATEGORIES = [
    "Sales", "Services", "Consulting", "Rent Received", "Transfers In", "Other"
]

def calculate_pita(taxable_income: float) -> float:
    """Calculate Personal Income Tax using progressive rates"""
    tax = 0
    remaining = taxable_income
    cumulative = 0
    
    for bracket_amount, rate in PITA_RATES:
        if remaining <= 0:
            break
        taxable_at_rate = min(remaining, bracket_amount)
        tax += taxable_at_rate * rate
        remaining -= taxable_at_rate
        cumulative += bracket_amount
    
    return round(tax, 2)

def calculate_cita(taxable_income: float, turnover: float) -> float:
    """Calculate Company Income Tax"""
    if turnover < 25000000:
        return round(taxable_income * CITA_RATE_SMALL, 2)
    return round(taxable_income * CITA_RATE_LARGE, 2)

def calculate_vat(sales: float) -> float:
    """Calculate VAT at 7.5%"""
    return round(sales * VAT_RATE, 2)

# ========================
# AUTH HELPER
# ========================

async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user["id"] = str(user["_id"])
        user.pop("_id", None)
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ========================
# AUTH ENDPOINTS
# ========================

@api_router.post("/auth/register")
async def register(user_data: UserRegister, response: Response):
    email = user_data.email.lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_doc = {
        "email": email,
        "password_hash": hash_password(user_data.password),
        "name": user_data.name,
        "business_type": user_data.business_type,
        "monthly_income_range": user_data.monthly_income_range,
        "subscription_plan": "starter",
        "onboarding_completed": False,
        "pidgin_mode": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    
    return {
        "id": user_id,
        "email": email,
        "name": user_data.name,
        "business_type": user_data.business_type,
        "monthly_income_range": user_data.monthly_income_range,
        "subscription_plan": "starter",
        "onboarding_completed": False,
        "pidgin_mode": False,
        "created_at": user_doc["created_at"]
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin, response: Response, request: Request):
    email = credentials.email.lower()
    identifier = f"{request.client.host}:{email}"
    
    # Check brute force lockout
    attempts = await db.login_attempts.find_one({"identifier": identifier})
    if attempts and attempts.get("count", 0) >= 5:
        lockout_time = attempts.get("last_attempt")
        if lockout_time:
            lockout_until = datetime.fromisoformat(lockout_time) + timedelta(minutes=15)
            if datetime.now(timezone.utc) < lockout_until:
                raise HTTPException(status_code=429, detail="Too many failed attempts. Try again in 15 minutes.")
            else:
                await db.login_attempts.delete_one({"identifier": identifier})
    
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        # Increment failed attempts
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {"$inc": {"count": 1}, "$set": {"last_attempt": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Clear failed attempts on success
    await db.login_attempts.delete_one({"identifier": identifier})
    
    user_id = str(user["_id"])
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    
    return {
        "id": user_id,
        "email": user["email"],
        "name": user["name"],
        "business_type": user["business_type"],
        "monthly_income_range": user.get("monthly_income_range", "0-100000"),
        "subscription_plan": user.get("subscription_plan", "starter"),
        "onboarding_completed": user.get("onboarding_completed", False),
        "pidgin_mode": user.get("pidgin_mode", False),
        "created_at": user["created_at"]
    }

@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logged out successfully"}

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "business_type": user.get("business_type", "freelancer"),
        "monthly_income_range": user.get("monthly_income_range", "0-100000"),
        "subscription_plan": user.get("subscription_plan", "starter"),
        "onboarding_completed": user.get("onboarding_completed", False),
        "pidgin_mode": user.get("pidgin_mode", False),
        "created_at": user.get("created_at", "")
    }

@api_router.post("/auth/refresh")
async def refresh_token(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        user_id = str(user["_id"])
        access_token = create_access_token(user_id, user["email"])
        response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
        return {"message": "Token refreshed"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

# ========================
# USER SETTINGS
# ========================

@api_router.put("/user/settings")
async def update_settings(request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    update_fields = {}
    
    if "pidgin_mode" in data:
        update_fields["pidgin_mode"] = data["pidgin_mode"]
    if "onboarding_completed" in data:
        update_fields["onboarding_completed"] = data["onboarding_completed"]
    if "business_type" in data:
        update_fields["business_type"] = data["business_type"]
    if "monthly_income_range" in data:
        update_fields["monthly_income_range"] = data["monthly_income_range"]
    
    if update_fields:
        await db.users.update_one({"_id": ObjectId(user["id"])}, {"$set": update_fields})
    
    return {"message": "Settings updated"}

@api_router.put("/user/subscription")
async def update_subscription(sub_data: SubscriptionUpdate, user: dict = Depends(get_current_user)):
    if sub_data.plan not in ["starter", "growth", "business"]:
        raise HTTPException(status_code=400, detail="Invalid subscription plan")
    
    await db.users.update_one(
        {"_id": ObjectId(user["id"])},
        {"$set": {"subscription_plan": sub_data.plan}}
    )
    return {"message": f"Subscription updated to {sub_data.plan}"}

# ========================
# BANK ACCOUNTS (MOCK)
# ========================

NIGERIAN_BANKS = [
    "GTBank", "Access Bank", "Zenith Bank", "First Bank", "UBA",
    "Kuda", "Opay", "Moniepoint", "Sterling Bank", "Stanbic IBTC"
]

@api_router.get("/banks")
async def get_supported_banks():
    return {"banks": NIGERIAN_BANKS}

@api_router.post("/bank-accounts")
async def link_bank_account(account_data: BankAccountCreate, user: dict = Depends(get_current_user)):
    # Check subscription - only Growth and Business can link banks
    if user.get("subscription_plan") == "starter":
        raise HTTPException(status_code=403, detail="Bank linking requires Growth or Business plan")
    
    # Mock bank linking - simulates read-only access
    account_doc = {
        "user_id": user["id"],
        "bank_name": account_data.bank_name,
        "account_number": account_data.account_number[-4:].rjust(10, "*"),  # Mask account number
        "account_name": account_data.account_name,
        "balance": round(50000 + (hash(account_data.account_number) % 500000), 2),  # Mock balance
        "linked": True,
        "last_synced": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.bank_accounts.insert_one(account_doc)
    
    # Generate mock transactions for the linked account
    await generate_mock_transactions(user["id"], str(result.inserted_id))
    
    return {
        "id": str(result.inserted_id),
        "user_id": user["id"],
        "bank_name": account_doc["bank_name"],
        "account_number": account_doc["account_number"],
        "account_name": account_doc["account_name"],
        "balance": account_doc["balance"],
        "linked": True,
        "last_synced": account_doc["last_synced"],
        "created_at": account_doc["created_at"]
    }

@api_router.get("/bank-accounts")
async def get_bank_accounts(user: dict = Depends(get_current_user)):
    accounts = await db.bank_accounts.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    # Add id field
    result = []
    async for acc in db.bank_accounts.find({"user_id": user["id"]}):
        result.append({
            "id": str(acc["_id"]),
            "user_id": acc["user_id"],
            "bank_name": acc["bank_name"],
            "account_number": acc["account_number"],
            "account_name": acc["account_name"],
            "balance": acc["balance"],
            "linked": acc["linked"],
            "last_synced": acc.get("last_synced"),
            "created_at": acc["created_at"]
        })
    return result

@api_router.delete("/bank-accounts/{account_id}")
async def unlink_bank_account(account_id: str, user: dict = Depends(get_current_user)):
    result = await db.bank_accounts.delete_one({"_id": ObjectId(account_id), "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Bank account not found")
    return {"message": "Bank account unlinked"}

async def generate_mock_transactions(user_id: str, bank_account_id: str):
    """Generate realistic mock transactions for a linked bank account"""
    import random
    
    mock_transactions = [
        {"type": "income", "category": "Sales", "description": "Payment from customer - Invoice #1234", "amount": 150000},
        {"type": "income", "category": "Services", "description": "Consulting fee - Project Alpha", "amount": 250000},
        {"type": "expense", "category": "Rent", "description": "Office rent - January", "amount": 80000},
        {"type": "expense", "category": "Utilities", "description": "PHCN Electricity bill", "amount": 15000},
        {"type": "expense", "category": "Transport", "description": "Bolt rides - Business meetings", "amount": 8500},
        {"type": "income", "category": "Consulting", "description": "Strategy consultation", "amount": 180000},
        {"type": "expense", "category": "Subscriptions", "description": "Google Workspace subscription", "amount": 5000},
        {"type": "expense", "category": "Marketing", "description": "Facebook Ads campaign", "amount": 25000},
        {"type": "income", "category": "Sales", "description": "Product sales - Week 2", "amount": 320000},
        {"type": "expense", "category": "Professional Fees", "description": "Legal consultation", "amount": 50000},
    ]
    
    transactions = []
    for i, tx in enumerate(mock_transactions):
        date = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))
        transactions.append({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "bank_account_id": bank_account_id,
            "amount": tx["amount"],
            "type": tx["type"],
            "category": tx["category"],
            "description": tx["description"],
            "date": date.isoformat(),
            "is_recurring": random.choice([True, False]),
            "ai_categorized": True,
            "flagged": random.random() < 0.1,  # 10% flagged for review
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    if transactions:
        await db.transactions.insert_many(transactions)

# ========================
# TRANSACTIONS
# ========================

@api_router.post("/transactions")
async def create_transaction(tx_data: TransactionCreate, user: dict = Depends(get_current_user)):
    tx_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "amount": tx_data.amount,
        "type": tx_data.type,
        "category": tx_data.category,
        "description": tx_data.description,
        "date": tx_data.date or datetime.now(timezone.utc).isoformat(),
        "bank_account_id": tx_data.bank_account_id,
        "is_recurring": False,
        "ai_categorized": False,
        "flagged": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.transactions.insert_one(tx_doc)
    tx_doc.pop("_id", None)
    return tx_doc

@api_router.get("/transactions")
async def get_transactions(
    type: Optional[str] = None,
    category: Optional[str] = None,
    flagged: Optional[bool] = None,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    query = {"user_id": user["id"]}
    if type:
        query["type"] = type
    if category:
        query["category"] = category
    if flagged is not None:
        query["flagged"] = flagged
    
    transactions = await db.transactions.find(query, {"_id": 0}).sort("date", -1).to_list(limit)
    return transactions

@api_router.put("/transactions/{tx_id}")
async def update_transaction(tx_id: str, request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    update_fields = {}
    
    for field in ["category", "description", "flagged", "is_recurring"]:
        if field in data:
            update_fields[field] = data[field]
    
    if update_fields:
        await db.transactions.update_one(
            {"id": tx_id, "user_id": user["id"]},
            {"$set": update_fields}
        )
    
    return {"message": "Transaction updated"}

@api_router.delete("/transactions/{tx_id}")
async def delete_transaction(tx_id: str, user: dict = Depends(get_current_user)):
    result = await db.transactions.delete_one({"id": tx_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted"}

# ========================
# DASHBOARD & TAX CALCULATIONS
# ========================

@api_router.get("/dashboard")
async def get_dashboard(user: dict = Depends(get_current_user)):
    user_id = user["id"]
    now = datetime.now(timezone.utc)
    
    # Get ALL transactions for the user (show all-time totals on dashboard)
    all_user_transactions = await db.transactions.find({"user_id": user_id}, {"_id": 0}).to_list(10000)
    
    # Use all transactions for totals (better UX)
    transactions = all_user_transactions
    
    # Calculate totals from all transactions
    total_income = sum(tx["amount"] for tx in transactions if tx["type"] == "income")
    total_expenses = sum(tx["amount"] for tx in transactions if tx["type"] == "expense")
    net_income = total_income - total_expenses
    
    # Get bank balances
    bank_accounts = await db.bank_accounts.find({"user_id": user_id}, {"_id": 0}).to_list(10)
    total_bank_balance = sum(acc.get("balance", 0) for acc in bank_accounts)
    
    # Calculate tax estimate based on business type
    business_type = user.get("business_type", "freelancer")
    deductible_expenses = total_expenses * 0.7  # Assume 70% deductible
    taxable_income = max(0, total_income - deductible_expenses)
    
    if business_type == "company":
        estimated_tax = calculate_cita(taxable_income, total_income * 12)
    else:
        estimated_tax = calculate_pita(taxable_income)
    
    vat_owed = calculate_vat(total_income) if business_type in ["sme", "company"] else 0
    
    # Calculate Tax Health Score (0-100)
    # Based on: categorization rate, receipt uploads, timely tracking
    categorized_count = sum(1 for tx in all_user_transactions if tx.get("category"))
    total_tx_count = len(all_user_transactions) or 1
    
    receipts = await db.receipts.count_documents({"user_id": user_id})
    
    categorization_score = (categorized_count / total_tx_count) * 40
    receipt_score = min(receipts * 5, 30)
    tracking_score = 30 if len(bank_accounts) > 0 else 15
    
    tax_health_score = min(100, int(categorization_score + receipt_score + tracking_score))
    
    # Spending breakdown by category
    spending_breakdown = {}
    for tx in transactions:
        if tx["type"] == "expense":
            cat = tx.get("category", "Miscellaneous")
            spending_breakdown[cat] = spending_breakdown.get(cat, 0) + tx["amount"]
    
    # Flagged transactions count
    flagged_count = await db.transactions.count_documents({"user_id": user_id, "flagged": True})
    
    # Upcoming deadlines
    next_vat_deadline = (now.replace(day=21) + timedelta(days=32)).replace(day=21)
    
    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_income": net_income,
        "total_bank_balance": total_bank_balance,
        "estimated_tax": estimated_tax,
        "vat_owed": vat_owed,
        "tax_health_score": tax_health_score,
        "spending_breakdown": spending_breakdown,
        "flagged_transactions_count": flagged_count,
        "bank_accounts_count": len(bank_accounts),
        "upcoming_deadlines": [
            {"name": "VAT Filing", "date": next_vat_deadline.strftime("%B %d, %Y")},
            {"name": "Annual Returns", "date": "March 31, 2026"}
        ],
        "business_type": business_type,
        "subscription_plan": user.get("subscription_plan", "starter")
    }

@api_router.get("/tax-calculation")
async def calculate_taxes(user: dict = Depends(get_current_user)):
    user_id = user["id"]
    business_type = user.get("business_type", "freelancer")
    
    # Get all transactions for the year
    year_start = datetime.now(timezone.utc).replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    transactions = await db.transactions.find({
        "user_id": user_id,
        "date": {"$gte": year_start.isoformat()}
    }, {"_id": 0}).to_list(10000)
    
    gross_income = sum(tx["amount"] for tx in transactions if tx["type"] == "income")
    total_expenses = sum(tx["amount"] for tx in transactions if tx["type"] == "expense")
    
    # Deductible expenses by category
    deductible_categories = ["Rent", "Utilities", "Professional Fees", "Marketing", "Equipment", "Subscriptions"]
    deductible_expenses = sum(
        tx["amount"] for tx in transactions 
        if tx["type"] == "expense" and tx.get("category") in deductible_categories
    )
    
    taxable_income = max(0, gross_income - deductible_expenses)
    
    # Calculate taxes
    if business_type == "company":
        income_tax = calculate_cita(taxable_income, gross_income)
        tax_type = "Company Income Tax (CITA)"
    else:
        income_tax = calculate_pita(taxable_income)
        tax_type = "Personal Income Tax (PITA)"
    
    vat = calculate_vat(gross_income) if business_type in ["sme", "company"] else 0
    
    # Potential savings
    non_deducted = total_expenses - deductible_expenses
    potential_savings = non_deducted * 0.2  # Estimate 20% savings if properly categorized
    
    return {
        "gross_income": gross_income,
        "total_expenses": total_expenses,
        "deductible_expenses": deductible_expenses,
        "taxable_income": taxable_income,
        "income_tax": income_tax,
        "tax_type": tax_type,
        "vat": vat,
        "total_tax_owed": income_tax + vat,
        "potential_savings": potential_savings,
        "business_type": business_type,
        "tax_brackets": PITA_RATES if business_type != "company" else None,
        "disclaimer": "This estimate is for guidance. Consult a certified tax professional for your final filing."
    }

# ========================
# RECEIPT SCANNER
# ========================

@api_router.post("/receipts/upload")
async def upload_receipt(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    if user.get("subscription_plan") == "starter":
        # Check upload limit for starter plan
        month_start = datetime.now(timezone.utc).replace(day=1)
        receipt_count = await db.receipts.count_documents({
            "user_id": user["id"],
            "created_at": {"$gte": month_start.isoformat()}
        })
        if receipt_count >= 10:
            raise HTTPException(status_code=403, detail="Starter plan limited to 10 receipts/month")
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Use JPEG, PNG, WebP, or PDF.")
    
    # Upload to storage
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    storage_path = f"{APP_NAME}/receipts/{user['id']}/{uuid.uuid4()}.{ext}"
    
    file_data = await file.read()
    try:
        result = put_object(storage_path, file_data, file.content_type)
    except Exception as e:
        logger.error(f"Receipt upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload receipt")
    
    # Store receipt record
    receipt_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "storage_path": result["path"],
        "original_filename": file.filename,
        "content_type": file.content_type,
        "size": result.get("size", len(file_data)),
        "extracted_data": None,  # Will be filled by AI
        "transaction_id": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.receipts.insert_one(receipt_doc)
    receipt_doc.pop("_id", None)
    
    return receipt_doc

@api_router.get("/receipts")
async def get_receipts(user: dict = Depends(get_current_user)):
    receipts = await db.receipts.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return receipts

@api_router.get("/receipts/{receipt_id}/download")
async def download_receipt(receipt_id: str, user: dict = Depends(get_current_user)):
    receipt = await db.receipts.find_one({"id": receipt_id, "user_id": user["id"]})
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    try:
        data, content_type = get_object(receipt["storage_path"])
        return Response(content=data, media_type=receipt.get("content_type", content_type))
    except Exception as e:
        logger.error(f"Receipt download failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to download receipt")

# ========================
# AI CHAT ASSISTANT
# ========================

@api_router.post("/chat")
async def chat_with_assistant(message: ChatMessage, user: dict = Depends(get_current_user)):
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    session_id = message.session_id or f"nairatrack-{user['id']}-{uuid.uuid4()}"
    
    system_message = f"""You are NairaTrack Tax Assistant, an expert on Nigerian tax laws and financial management.
    You help Nigerian freelancers, SMEs, and companies understand:
    - Personal Income Tax (PITA) rates (7% to 24% progressive)
    - Company Income Tax (CITA) at 20% for small companies (<₦25M) or 30% for larger ones
    - VAT at 7.5%
    - Withholding Tax (WHT) rates
    - FIRS filing requirements and deadlines
    - Tax-deductible expenses
    - Finance Act 2023/2024 changes
    
    The user is a {user.get('business_type', 'freelancer')} with subscription plan: {user.get('subscription_plan', 'starter')}.
    
    Be friendly, clear, and use simple language. If asked, you can respond in Nigerian Pidgin.
    Always include practical examples with Naira amounts (₦).
    Add disclaimer for complex tax situations to consult a certified tax professional."""
    
    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=system_message
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        
        user_message = UserMessage(text=message.message)
        response = await chat.send_message(user_message)
        
        # Store chat history
        await db.chat_history.insert_one({
            "user_id": user["id"],
            "session_id": session_id,
            "user_message": message.message,
            "assistant_response": response,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "response": response,
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get AI response")

@api_router.get("/chat/history")
async def get_chat_history(session_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {"user_id": user["id"]}
    if session_id:
        query["session_id"] = session_id
    
    history = await db.chat_history.find(query, {"_id": 0}).sort("created_at", -1).to_list(50)
    return history

# ========================
# TAX FILING GUIDE
# ========================

@api_router.get("/tax-filing/guide")
async def get_filing_guide(user: dict = Depends(get_current_user)):
    business_type = user.get("business_type", "freelancer")
    
    common_steps = [
        {"step": 1, "title": "Register on TaxPro-Max", "description": "Visit taxpromax.firs.gov.ng and create an account with your TIN"},
        {"step": 2, "title": "Gather Documents", "description": "Prepare income statements, expense receipts, and bank statements"},
        {"step": 3, "title": "Calculate Taxable Income", "description": "Use NairaTrack's tax calculator for accurate estimates"},
        {"step": 4, "title": "Complete Tax Return", "description": "Fill in the appropriate forms on TaxPro-Max portal"},
        {"step": 5, "title": "Submit and Pay", "description": "Submit your return and pay any tax owed via bank transfer or card"}
    ]
    
    documents_needed = [
        "Tax Identification Number (TIN)",
        "Bank statements for the tax year",
        "Income receipts and invoices",
        "Expense receipts (properly categorized)",
        "Previous year's tax returns (if any)",
        "Business registration documents"
    ]
    
    if business_type == "company":
        documents_needed.extend([
            "Certificate of Incorporation",
            "Audited Financial Statements",
            "Board Resolution for tax filing"
        ])
    
    deadlines = {
        "vat": "21st of the following month",
        "paye": "10th of the following month",
        "annual_cit": "6 months after financial year end",
        "annual_pit": "March 31st"
    }
    
    return {
        "steps": common_steps,
        "documents_needed": documents_needed,
        "deadlines": deadlines,
        "firs_portal": "https://taxpromax.firs.gov.ng",
        "business_type": business_type
    }

@api_router.get("/tax-filing/checklist")
async def get_filing_checklist(user: dict = Depends(get_current_user)):
    user_id = user["id"]
    
    # Check what the user has done
    transactions = await db.transactions.count_documents({"user_id": user_id})
    receipts = await db.receipts.count_documents({"user_id": user_id})
    bank_accounts = await db.bank_accounts.count_documents({"user_id": user_id})
    
    checklist = [
        {"item": "Create NairaTrack account", "completed": True},
        {"item": "Set business type", "completed": user.get("business_type") is not None},
        {"item": "Link bank account", "completed": bank_accounts > 0},
        {"item": "Track at least 10 transactions", "completed": transactions >= 10},
        {"item": "Upload expense receipts", "completed": receipts > 0},
        {"item": "Review flagged transactions", "completed": False},
        {"item": "Generate tax report", "completed": False},
        {"item": "Register on FIRS TaxPro-Max", "completed": False}
    ]
    
    completed_count = sum(1 for item in checklist if item["completed"])
    
    return {
        "checklist": checklist,
        "completed_count": completed_count,
        "total_count": len(checklist),
        "progress_percentage": int((completed_count / len(checklist)) * 100)
    }

# ========================
# TAX EDUCATION ARTICLES
# ========================

TAX_ARTICLES = [
    {
        "id": "1",
        "title": "Understanding PITA: Personal Income Tax in Nigeria",
        "summary": "Learn how personal income tax works for freelancers and self-employed individuals",
        "content": """
Personal Income Tax Act (PITA) applies to individuals, sole proprietorships, and partnerships in Nigeria.

**Tax Rates (Progressive):**
- First ₦300,000: 7%
- Next ₦300,000: 11%
- Next ₦500,000: 15%
- Next ₦500,000: 19%
- Next ₦1,600,000: 21%
- Above ₦3,200,000: 24%

**Who Pays PITA?**
- Freelancers and consultants
- Self-employed professionals
- Sole proprietors
- Partners in partnerships

**Filing Deadline:** March 31st of the following year
        """,
        "category": "basics"
    },
    {
        "id": "2",
        "title": "VAT in Nigeria: Everything You Need to Know",
        "summary": "A complete guide to Value Added Tax at 7.5% for Nigerian businesses",
        "content": """
Value Added Tax (VAT) is charged at 7.5% on most goods and services in Nigeria.

**VAT Registration:**
- Mandatory for businesses with turnover above threshold
- Must register within 6 months of commencing business

**Filing:**
- Monthly filing required
- Due by 21st of the following month
- File via TaxPro-Max portal

**VAT Exempt Items:**
- Basic food items
- Medical and pharmaceutical products
- Educational materials
- Baby products
        """,
        "category": "vat"
    },
    {
        "id": "3",
        "title": "Tax Deductible Expenses: Maximize Your Savings",
        "summary": "Learn which business expenses can reduce your tax bill",
        "content": """
Properly recording deductible expenses can significantly reduce your tax liability.

**Common Deductible Expenses:**
- Office rent and utilities
- Employee salaries and benefits
- Professional services (legal, accounting)
- Marketing and advertising
- Business travel and transport
- Equipment and supplies
- Insurance premiums
- Bank charges and interest

**Documentation Required:**
- Keep all receipts and invoices
- Maintain proper records for 6 years
- Ensure expenses are wholly and exclusively for business
        """,
        "category": "deductions"
    },
    {
        "id": "4",
        "title": "Finance Act 2023/2024: Key Changes",
        "summary": "Important updates from recent Nigerian tax legislation",
        "content": """
The Finance Acts of 2023 and 2024 introduced several changes:

**Key Changes:**
- VAT rate remains at 7.5%
- New exemptions for small businesses
- Digital services taxation framework
- Updated transfer pricing rules
- Revised penalties for late filing

**Impact on Businesses:**
- More emphasis on electronic filing
- Stricter compliance requirements
- New incentives for SMEs
        """,
        "category": "updates"
    }
]

@api_router.get("/education/articles")
async def get_education_articles(category: Optional[str] = None):
    if category:
        return [a for a in TAX_ARTICLES if a["category"] == category]
    return TAX_ARTICLES

@api_router.get("/education/articles/{article_id}")
async def get_article(article_id: str):
    for article in TAX_ARTICLES:
        if article["id"] == article_id:
            return article
    raise HTTPException(status_code=404, detail="Article not found")

# ========================
# REPORTS & EXPORT
# ========================

@api_router.get("/reports/summary")
async def get_report_summary(period: str = "month", user: dict = Depends(get_current_user)):
    user_id = user["id"]
    now = datetime.now(timezone.utc)
    
    if period == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "year":
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = now - timedelta(days=30)
    
    transactions = await db.transactions.find({
        "user_id": user_id,
        "date": {"$gte": start_date.isoformat()}
    }, {"_id": 0}).to_list(10000)
    
    income_by_category = {}
    expense_by_category = {}
    
    for tx in transactions:
        cat = tx.get("category", "Other")
        if tx["type"] == "income":
            income_by_category[cat] = income_by_category.get(cat, 0) + tx["amount"]
        else:
            expense_by_category[cat] = expense_by_category.get(cat, 0) + tx["amount"]
    
    total_income = sum(income_by_category.values())
    total_expenses = sum(expense_by_category.values())
    
    return {
        "period": period,
        "start_date": start_date.isoformat(),
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_profit": total_income - total_expenses,
        "income_by_category": income_by_category,
        "expense_by_category": expense_by_category,
        "transaction_count": len(transactions)
    }

# ========================
# CATEGORIES
# ========================

@api_router.get("/categories")
async def get_categories():
    return {
        "income": INCOME_CATEGORIES,
        "expense": EXPENSE_CATEGORIES
    }

# ========================
# HEALTH CHECK
# ========================

@api_router.get("/")
async def root():
    return {"message": "NairaTrack API is running", "version": "1.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include the router in the main app
app.include_router(api_router)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[os.environ.get('FRONTEND_URL', 'http://localhost:3000'), "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def startup():
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.login_attempts.create_index("identifier")
    await db.transactions.create_index([("user_id", 1), ("date", -1)])
    await db.bank_accounts.create_index("user_id")
    await db.receipts.create_index("user_id")
    await db.chat_history.create_index([("user_id", 1), ("session_id", 1)])
    
    # Initialize storage
    try:
        init_storage()
        logger.info("Storage initialized successfully")
    except Exception as e:
        logger.warning(f"Storage init warning: {e}")
    
    # Seed admin user
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@nairatrack.ng")
    admin_password = os.environ.get("ADMIN_PASSWORD", "NairaTrack2024!")
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "name": "Admin",
            "business_type": "company",
            "monthly_income_range": "1000000+",
            "subscription_plan": "business",
            "onboarding_completed": True,
            "pidgin_mode": False,
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Admin user created: {admin_email}")
    
    # Write test credentials
    from pathlib import Path
    Path("/app/memory").mkdir(parents=True, exist_ok=True)
    with open("/app/memory/test_credentials.md", "w") as f:
        f.write(f"""# NairaTrack Test Credentials

## Admin Account
- Email: {admin_email}
- Password: {admin_password}
- Role: admin

## Test User (create via registration)
- Register with any email/password
- Default plan: Starter

## API Endpoints
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/me
- GET /api/dashboard
- GET /api/transactions
- POST /api/transactions
- GET /api/bank-accounts
- POST /api/bank-accounts
- GET /api/tax-calculation
- POST /api/chat
- POST /api/receipts/upload
""")
    
    logger.info("NairaTrack API started successfully")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
