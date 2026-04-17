import uuid
import os
import hmac
import hashlib
import logging
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request

from database import db
from config import MONO_SECRET_KEY, MONO_PUBLIC_KEY, MONO_WEBHOOK_SECRET, MONO_API_BASE, NIGERIAN_BANKS
from models import BankAccountCreate, MonoLinkRequest
from utils.auth import get_current_user
from routes.transactions import generate_mock_transactions

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/banks")
async def get_supported_banks():
    return {"banks": NIGERIAN_BANKS}


@router.post("/bank-accounts")
async def link_bank_account(account_data: BankAccountCreate, user: dict = Depends(get_current_user)):
    if user.get("subscription_plan") == "starter":
        raise HTTPException(status_code=403, detail="Bank linking requires Growth or Business plan")

    account_doc = {
        "user_id": user["id"],
        "bank_name": account_data.bank_name,
        "account_number": account_data.account_number[-4:].rjust(10, "*"),
        "account_name": account_data.account_name,
        "balance": round(50000 + (hash(account_data.account_number) % 500000), 2),
        "linked": True,
        "last_synced": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    result = await db.bank_accounts.insert_one(account_doc)
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


@router.get("/bank-accounts")
async def get_bank_accounts(user: dict = Depends(get_current_user)):
    result = []
    async for acc in db.bank_accounts.find({"user_id": user["id"]}).limit(50):
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


@router.delete("/bank-accounts/{account_id}")
async def unlink_bank_account(account_id: str, user: dict = Depends(get_current_user)):
    from bson import ObjectId
    result = await db.bank_accounts.delete_one({"_id": ObjectId(account_id), "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Bank account not found")
    return {"message": "Bank account unlinked"}


def categorize_transaction(narration: str) -> str:
    narration_lower = narration.lower()
    if any(word in narration_lower for word in ["salary", "wage", "pay"]):
        return "Salaries"
    elif any(word in narration_lower for word in ["rent", "housing", "accommodation"]):
        return "Rent"
    elif any(word in narration_lower for word in ["electricity", "phcn", "nepa", "water", "dstv", "gotv"]):
        return "Utilities"
    elif any(word in narration_lower for word in ["uber", "bolt", "taxi", "fuel", "petrol", "transport"]):
        return "Transport"
    elif any(word in narration_lower for word in ["google", "microsoft", "netflix", "spotify", "subscription"]):
        return "Subscriptions"
    elif any(word in narration_lower for word in ["facebook", "instagram", "ads", "marketing", "advert"]):
        return "Marketing"
    elif any(word in narration_lower for word in ["transfer", "credit", "received"]):
        return "Transfers In"
    elif any(word in narration_lower for word in ["pos", "atm", "withdrawal"]):
        return "Miscellaneous"
    return "Miscellaneous"


@router.post("/mono/initiate-linking")
async def initiate_mono_linking(data: MonoLinkRequest, user: dict = Depends(get_current_user)):
    if user.get("subscription_plan") == "starter":
        raise HTTPException(status_code=403, detail="Bank linking requires Growth or Business plan")

    if not MONO_SECRET_KEY:
        return {"mode": "mock", "message": "Mono integration not configured. Using mock bank linking.", "mock_url": None}

    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "customer": user.get("mono_customer_id") or user["id"],
                "meta": {"user_id": user["id"], "email": user["email"]},
                "scope": "auth",
                "redirect_url": os.environ.get("FRONTEND_URL", "http://localhost:3000") + "/settings?bank_linked=true"
            }
            if data.institution_id:
                payload["institution"] = data.institution_id

            response = await client.post(
                f"{MONO_API_BASE}/accounts/initiate",
                headers={"mono-sec-key": MONO_SECRET_KEY, "Content-Type": "application/json"},
                json=payload, timeout=30.0
            )
            result = response.json()

        if result.get("status") == "successful":
            return {"mode": "live", "mono_url": result["data"]["mono_url"], "session_id": result["data"].get("id")}

        raise HTTPException(status_code=400, detail=result.get("message", "Failed to initiate bank linking"))
    except httpx.HTTPError as e:
        logger.error(f"Mono initiate error: {e}")
        return {"mode": "mock", "message": "Bank linking service unavailable. Using simulated mode.", "mock_url": None}


@router.post("/mono/exchange-token")
async def exchange_mono_token(request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    code = data.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code required")
    if not MONO_SECRET_KEY:
        raise HTTPException(status_code=400, detail="Mono not configured")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MONO_API_BASE}/accounts/auth",
                headers={"mono-sec-key": MONO_SECRET_KEY, "Content-Type": "application/json"},
                json={"code": code}, timeout=30.0
            )
            result = response.json()

        if result.get("status") == "successful":
            account_id = result["data"]["id"]
            account_doc = {
                "user_id": user["id"],
                "mono_account_id": account_id,
                "bank_name": result["data"].get("institution", {}).get("name", "Unknown"),
                "account_number": result["data"].get("account_number", "****"),
                "account_name": result["data"].get("name", user["name"]),
                "balance": result["data"].get("balance", 0) / 100,
                "linked": True,
                "data_status": result["data"].get("meta", {}).get("data_status", "processing"),
                "last_synced": datetime.now(timezone.utc).isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.bank_accounts.insert_one(account_doc)
            logger.info(f"Mono account linked for user {user['email']}: {account_id}")
            return {"status": "success", "account_id": account_id, "bank_name": account_doc["bank_name"]}

        raise HTTPException(status_code=400, detail=result.get("message", "Token exchange failed"))
    except httpx.HTTPError as e:
        logger.error(f"Mono token exchange error: {e}")
        raise HTTPException(status_code=500, detail="Failed to link bank account")


@router.get("/mono/account/{account_id}/transactions")
async def get_mono_transactions(account_id: str, user: dict = Depends(get_current_user)):
    account = await db.bank_accounts.find_one({"mono_account_id": account_id, "user_id": user["id"]})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if not MONO_SECRET_KEY:
        raise HTTPException(status_code=400, detail="Mono not configured")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MONO_API_BASE}/accounts/{account_id}/transactions",
                headers={"mono-sec-key": MONO_SECRET_KEY, "x-real-time": "true"},
                params={"paginate": False}, timeout=30.0
            )
            result = response.json()

        if result.get("status") == "successful":
            transactions = result.get("data", [])
            for tx in transactions:
                existing = await db.transactions.find_one({"mono_transaction_id": tx.get("_id")})
                if not existing:
                    tx_doc = {
                        "id": str(uuid.uuid4()),
                        "user_id": user["id"],
                        "bank_account_id": account_id,
                        "mono_transaction_id": tx.get("_id"),
                        "amount": abs(tx.get("amount", 0)) / 100,
                        "type": "income" if tx.get("type") == "credit" else "expense",
                        "category": categorize_transaction(tx.get("narration", "")),
                        "description": tx.get("narration", "Bank transaction"),
                        "date": tx.get("date", datetime.now(timezone.utc).isoformat()),
                        "is_recurring": False,
                        "ai_categorized": True,
                        "flagged": False,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    await db.transactions.insert_one(tx_doc)
            return {"status": "success", "transactions_count": len(transactions), "imported": True}

        return {"status": "failed", "message": result.get("message")}
    except httpx.HTTPError as e:
        logger.error(f"Mono transactions error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch transactions")


@router.get("/mono/account/{account_id}/balance")
async def get_mono_balance(account_id: str, user: dict = Depends(get_current_user)):
    account = await db.bank_accounts.find_one({"mono_account_id": account_id, "user_id": user["id"]})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if not MONO_SECRET_KEY:
        return {"balance": account.get("balance", 0), "real_time": False}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MONO_API_BASE}/accounts/{account_id}/balance",
                headers={"mono-sec-key": MONO_SECRET_KEY, "x-real-time": "true"},
                timeout=30.0
            )
            result = response.json()

        if result.get("status") == "successful":
            balance = result["data"].get("balance", 0) / 100
            await db.bank_accounts.update_one(
                {"mono_account_id": account_id},
                {"$set": {"balance": balance, "last_synced": datetime.now(timezone.utc).isoformat()}}
            )
            return {"balance": balance, "real_time": True}

        return {"balance": account.get("balance", 0), "real_time": False}
    except httpx.HTTPError as e:
        logger.error(f"Mono balance error: {e}")
        return {"balance": account.get("balance", 0), "real_time": False}


@router.post("/mono/webhook")
async def mono_webhook(request: Request):
    signature = request.headers.get("mono-webhook-secret")
    body = await request.body()

    if MONO_WEBHOOK_SECRET and signature:
        computed = hmac.new(MONO_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(computed, signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    event = await request.json()
    event_type = event.get("event")
    data = event.get("data", {})
    logger.info(f"Mono webhook received: {event_type}")

    if event_type == "mono.events.account_connected":
        account_id = data.get("id")
        await db.bank_accounts.update_one(
            {"mono_account_id": account_id},
            {"$set": {"data_status": "available"}}
        )
    elif event_type == "mono.events.account_updated":
        account_id = data.get("id")
        data_status = data.get("meta", {}).get("data_status")
        await db.bank_accounts.update_one(
            {"mono_account_id": account_id},
            {"$set": {"data_status": data_status}}
        )

    return {"status": "ok"}


@router.get("/mono/config")
async def get_mono_config():
    return {"public_key": MONO_PUBLIC_KEY, "configured": bool(MONO_SECRET_KEY and MONO_PUBLIC_KEY)}
