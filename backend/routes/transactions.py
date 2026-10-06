import uuid
import re
import random
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional

from database import db
from models import TransactionCreate
from utils.auth import get_current_user
from config import EXPENSE_CATEGORIES, INCOME_CATEGORIES

logger = logging.getLogger(__name__)

router = APIRouter()

AMOUNT_TOLERANCE = 0.02  # ±2%
DATE_WINDOW_HOURS = 24


def _extract_account_number(description: str) -> Optional[str]:
    """Extract a 10-digit Nigerian account number from description."""
    match = re.search(r'\b\d{10}\b', description or "")
    return match.group(0) if match else None


def _descriptions_overlap(a: str, b: str) -> bool:
    """Check if two descriptions are similar enough to be duplicates."""
    a, b = (a or "").lower().strip(), (b or "").lower().strip()
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    words_a = set(a.split())
    words_b = set(b.split())
    if not words_a or not words_b:
        return False
    overlap = len(words_a & words_b) / max(len(words_a), len(words_b))
    return overlap >= 0.7


async def _find_duplicate(user_id: str, amount: float, date_str: str, description: str, counterparty: Optional[str] = None):
    """Check if a near-duplicate transaction already exists."""
    try:
        tx_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        tx_date = datetime.now(timezone.utc)

    window_start = (tx_date - timedelta(hours=DATE_WINDOW_HOURS)).isoformat()
    window_end = (tx_date + timedelta(hours=DATE_WINDOW_HOURS)).isoformat()
    lo = amount * (1 - AMOUNT_TOLERANCE)
    hi = amount * (1 + AMOUNT_TOLERANCE)

    candidates = await db.transactions.find({
        "user_id": user_id,
        "amount": {"$gte": lo, "$lte": hi},
        "date": {"$gte": window_start, "$lte": window_end}
    }, {"_id": 0}).to_list(20)

    for c in candidates:
        # Match by counterparty account if available
        if counterparty:
            c_acct = c.get("counterparty_account") or _extract_account_number(c.get("description", ""))
            if c_acct == counterparty:
                return c
        # Match by description similarity
        if _descriptions_overlap(c.get("description", ""), description):
            return c
    return None


@router.post("/transactions")
async def create_transaction(tx_data: TransactionCreate, user: dict = Depends(get_current_user)):
    date_str = tx_data.date or datetime.now(timezone.utc).isoformat()
    counterparty = tx_data.counterparty_account or _extract_account_number(tx_data.description)

    # Duplicate detection
    existing = await _find_duplicate(user["id"], tx_data.amount, date_str, tx_data.description, counterparty)
    if existing:
        # If new description is more detailed, update the existing one
        if len(tx_data.description) > len(existing.get("description", "")):
            await db.transactions.update_one(
                {"id": existing["id"], "user_id": user["id"]},
                {"$set": {"description": tx_data.description}}
            )
            existing["description"] = tx_data.description
            return {**existing, "duplicate_merged": True, "message": "Updated existing transaction with more detail"}
        return {**existing, "duplicate_skipped": True, "message": "Duplicate transaction detected — skipped"}

    tx_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "amount": tx_data.amount,
        "type": tx_data.type,
        "category": tx_data.category,
        "description": tx_data.description,
        "date": date_str,
        "bank_account_id": tx_data.bank_account_id,
        "counterparty_account": counterparty,
        "is_recurring": False,
        "ai_categorized": False,
        "flagged": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.transactions.insert_one(tx_doc)
    tx_doc.pop("_id", None)

    # Update transaction memory
    if counterparty:
        await _update_memory(user["id"], counterparty, tx_data.category, tx_data.amount, tx_data.description)

    return tx_doc


async def _update_memory(user_id: str, counterparty: str, category: str, amount: float, description: str):
    """Update or create transaction memory for a counterparty."""
    mem = await db.transaction_memory.find_one({"user_id": user_id, "counterparty_account": counterparty})
    now = datetime.now(timezone.utc).isoformat()

    if mem:
        new_count = mem.get("occurrence_count", 0) + 1
        old_avg = mem.get("average_amount", 0)
        new_avg = round(((old_avg * (new_count - 1)) + amount) / new_count, 2)
        update = {
            "occurrence_count": new_count,
            "average_amount": new_avg,
            "last_seen": now,
        }
        # Auto-escalate lock based on consistency
        if category == mem.get("category"):
            new_confidence = mem.get("confidence_score", 0) + 1
            update["confidence_score"] = new_confidence
            if new_confidence >= 3 and mem.get("lock_status") != "hard":
                update["lock_status"] = "hard"
            elif new_count >= 2 and mem.get("lock_status") == "none":
                update["lock_status"] = "soft"
        await db.transaction_memory.update_one(
            {"user_id": user_id, "counterparty_account": counterparty},
            {"$set": update}
        )
    else:
        # Extract a name from description
        name = description.split(" to ")[-1].split(" for ")[0].strip() if " to " in description else description[:40]
        await db.transaction_memory.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "counterparty_account": counterparty,
            "counterparty_name": name,
            "category": category,
            "lock_status": "none",
            "confidence_score": 0,
            "occurrence_count": 1,
            "average_amount": amount,
            "last_seen": now
        })


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
        result = await db.transactions.update_one(
            {"id": tx_id, "user_id": user["id"]},
            {"$set": update_fields}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Transaction not found")
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


# ========================
# DUPLICATE DETECTION
# ========================

@router.get("/transactions/duplicates")
async def get_duplicates(user: dict = Depends(get_current_user)):
    """Scan transactions for potential duplicates."""
    all_txs = await db.transactions.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).sort("date", -1).to_list(2000)

    duplicates = []
    seen = set()
    for i, tx in enumerate(all_txs):
        if tx["id"] in seen:
            continue
        for j in range(i + 1, len(all_txs)):
            other = all_txs[j]
            if other["id"] in seen:
                continue
            # Check amount within ±2%
            if tx["amount"] == 0:
                continue
            ratio = abs(tx["amount"] - other["amount"]) / tx["amount"]
            if ratio > AMOUNT_TOLERANCE:
                continue
            # Check date within 24h
            try:
                d1 = datetime.fromisoformat(tx["date"].replace("Z", "+00:00"))
                d2 = datetime.fromisoformat(other["date"].replace("Z", "+00:00"))
                if abs((d1 - d2).total_seconds()) > DATE_WINDOW_HOURS * 3600:
                    continue
            except Exception:
                continue
            # Check description overlap or same counterparty
            acct1 = tx.get("counterparty_account") or _extract_account_number(tx.get("description", ""))
            acct2 = other.get("counterparty_account") or _extract_account_number(other.get("description", ""))
            if (acct1 and acct2 and acct1 == acct2) or _descriptions_overlap(tx.get("description", ""), other.get("description", "")):
                seen.add(other["id"])
                duplicates.append({
                    "original": tx,
                    "duplicate": other,
                    "reason": "Same counterparty" if (acct1 and acct1 == acct2) else "Similar description"
                })
    return {"duplicates": duplicates, "count": len(duplicates)}


@router.post("/transactions/cleanup-duplicates")
async def cleanup_duplicates(user: dict = Depends(get_current_user)):
    """Auto-remove duplicates keeping the more descriptive entry."""
    result = await get_duplicates(user)
    removed = 0
    for pair in result["duplicates"]:
        orig = pair["original"]
        dupe = pair["duplicate"]
        # Keep the one with longer description
        keep, remove = (orig, dupe) if len(orig.get("description", "")) >= len(dupe.get("description", "")) else (dupe, orig)
        await db.transactions.delete_one({"id": remove["id"], "user_id": user["id"]})
        removed += 1
    return {"removed": removed, "message": f"Cleaned up {removed} duplicate transactions"}


# ========================
# TRANSACTION MEMORY API
# ========================

@router.get("/transaction-memory")
async def get_transaction_memory(user: dict = Depends(get_current_user)):
    """List all transaction memory entries (soft/hard locked)."""
    memories = await db.transaction_memory.find(
        {"user_id": user["id"], "lock_status": {"$ne": "none"}},
        {"_id": 0}
    ).sort("last_seen", -1).to_list(200)
    return memories


@router.get("/transaction-memory/check")
async def check_memory(counterparty_account: str, user: dict = Depends(get_current_user)):
    """Check memory for a specific counterparty before categorization."""
    mem = await db.transaction_memory.find_one(
        {"user_id": user["id"], "counterparty_account": counterparty_account},
        {"_id": 0}
    )
    if not mem:
        return {"found": False}
    return {"found": True, **mem}


@router.put("/transaction-memory/{memory_id}")
async def update_memory(memory_id: str, request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    update = {}
    if "category" in data:
        update["category"] = data["category"]
    if "lock_status" in data:
        update["lock_status"] = data["lock_status"]
    if update:
        await db.transaction_memory.update_one(
            {"id": memory_id, "user_id": user["id"]},
            {"$set": update}
        )
    return {"message": "Memory updated"}


@router.delete("/transaction-memory/{memory_id}")
async def delete_memory(memory_id: str, user: dict = Depends(get_current_user)):
    result = await db.transaction_memory.delete_one({"id": memory_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return {"message": "Memory entry deleted"}


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
            "counterparty_account": None,
            "is_recurring": random.choice([True, False]),
            "ai_categorized": True,
            "flagged": random.random() < 0.1,
            "created_at": datetime.now(timezone.utc).isoformat()
        })

    if transactions:
        await db.transactions.insert_many(transactions)
