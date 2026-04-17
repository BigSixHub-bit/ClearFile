import uuid
import random
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional

from database import db
from models import TransactionCreate
from utils.auth import get_current_user
from config import EXPENSE_CATEGORIES, INCOME_CATEGORIES

router = APIRouter()


@router.post("/transactions")
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


@router.get("/transactions")
async def get_transactions(
    type: Optional[str] = None,
    category: Optional[str] = None,
    flagged: Optional[bool] = None,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    limit = min(limit, 1000)
    query = {"user_id": user["id"]}
    if type:
        query["type"] = type
    if category:
        query["category"] = category
    if flagged is not None:
        query["flagged"] = flagged
    return await db.transactions.find(query, {"_id": 0}).sort("date", -1).to_list(limit)


@router.put("/transactions/{tx_id}")
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


@router.delete("/transactions/{tx_id}")
async def delete_transaction(tx_id: str, user: dict = Depends(get_current_user)):
    result = await db.transactions.delete_one({"id": tx_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted"}


@router.get("/categories")
async def get_categories():
    return {"income": INCOME_CATEGORIES, "expense": EXPENSE_CATEGORIES}


async def generate_mock_transactions(user_id: str, bank_account_id: str):
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
    for tx in mock_transactions:
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
            "flagged": random.random() < 0.1,
            "created_at": datetime.now(timezone.utc).isoformat()
        })

    if transactions:
        await db.transactions.insert_many(transactions)
