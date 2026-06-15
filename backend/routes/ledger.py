"""AI Guide Payment (Flutterwave) + Invoice & Ledger system"""
import uuid
import logging
import hmac
import hashlib
import os
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request
from bson import ObjectId

from database import db
from utils.auth import get_current_user
from utils.flutterwave import flw_request, is_flutterwave_configured

logger = logging.getLogger(__name__)

router = APIRouter()

AI_GUIDE_PRICE = 70000  # ₦70,000
FRONTEND_URL = os.environ.get("FRONTEND_URL")
FLW_WEBHOOK_SECRET = os.environ.get("FLW_WEBHOOK_SECRET_HASH", "")


# ========================
# AI GUIDE PAYMENT (Flutterwave V4)
# ========================

@router.post("/payments/ai-guide/initialize")
async def initialize_ai_guide_payment(request: Request, user: dict = Depends(get_current_user)):
    """Initialize Flutterwave payment for AI Guide unlock (₦70,000)."""
    data = await request.json()
    callback_url = data.get("callback_url", f"{FRONTEND_URL}/payment-success")
    tx_ref = f"cfng_aiguide_{uuid.uuid4().hex[:16]}"

    existing = await db.ai_guide_unlocks.find_one({"user_id": user["id"], "status": "active"})
    if existing:
        return {"already_unlocked": True, "message": "AI Guide already unlocked"}

    if not is_flutterwave_configured():
        await db.ai_guide_unlocks.insert_one({
            "user_id": user["id"], "reference": tx_ref,
            "amount": AI_GUIDE_PRICE, "status": "active", "mode": "mock",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        return {"mock": True, "unlocked": True, "message": "AI Guide unlocked (demo mode)"}

    try:
        fw_payload = {
            "tx_ref": tx_ref,
            "amount": AI_GUIDE_PRICE,
            "currency": "NGN",
            "redirect_url": callback_url,
            "payment_options": "card,banktransfer,ussd",
            "customer": {"email": user["email"], "name": user.get("name", "")},
            "customizations": {"title": "ClearFile NG", "description": "AI Tax Filing Guide - One-time Unlock"},
            "meta": {"user_id": user["id"], "product": "ai_guide"}
        }

        response = await flw_request("POST", "/v3/payments", json=fw_payload)
        result = response.json()

        if response.status_code < 400 and result.get("data", {}).get("link"):
            await db.ai_guide_unlocks.insert_one({
                "user_id": user["id"], "reference": tx_ref,
                "amount": AI_GUIDE_PRICE, "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            return {"payment_link": result["data"]["link"], "tx_ref": tx_ref}

        logger.error(f"Flutterwave init response: {result}")
        raise HTTPException(status_code=400, detail=result.get("message", "Payment init failed"))
    except HTTPException:
        raise
    except Exception as e:
        msg = str(e)
        if "authentication failed" in msg.lower() or "credentials" in msg.lower():
            logger.error(f"Flutterwave auth error: {e}")
            raise HTTPException(status_code=424, detail="Payment gateway authentication failed. Contact admin to verify Flutterwave API credentials.")
        logger.error(f"Flutterwave AI guide error: {e}")
        raise HTTPException(status_code=500, detail="Payment service unavailable")


@router.get("/payments/ai-guide/verify")
async def verify_ai_guide_payment(transaction_id: str = None, tx_ref: str = None, user: dict = Depends(get_current_user)):
    """Verify AI Guide payment via Flutterwave."""
    if not is_flutterwave_configured():
        return {"status": "success", "unlocked": True, "mode": "mock"}

    if not transaction_id:
        raise HTTPException(status_code=400, detail="transaction_id required")

    try:
        response = await flw_request("GET", f"/v3/transactions/{transaction_id}/verify")
        result = response.json()
        data = result.get("data", {})

        if data.get("status") == "successful" and data.get("amount", 0) >= AI_GUIDE_PRICE and data.get("currency") == "NGN":
            ref = data.get("tx_ref", tx_ref)
            await db.ai_guide_unlocks.update_one(
                {"reference": ref},
                {"$set": {"status": "active", "transaction_id": transaction_id, "verified_at": datetime.now(timezone.utc).isoformat()}}
            )
            return {"status": "success", "unlocked": True}

        return {"status": "failed", "message": "Payment verification failed"}
    except Exception as e:
        logger.error(f"Flutterwave verify error: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")


@router.get("/payments/ai-guide/status")
async def get_ai_guide_status(user: dict = Depends(get_current_user)):
    """Check if user has unlocked the AI Guide."""
    unlock = await db.ai_guide_unlocks.find_one({"user_id": user["id"], "status": "active"})
    return {"unlocked": unlock is not None}


# ========================
# INVOICE SYSTEM
# ========================

@router.post("/invoices")
async def create_invoice(request: Request, user: dict = Depends(get_current_user)):
    """Create an invoice with line items."""
    data = await request.json()
    items = data.get("items", [])
    customer_name = data.get("customer_name", "")
    customer_phone = data.get("customer_phone", "")
    due_date = data.get("due_date")
    vat_enabled = data.get("vat_enabled", False)

    if not customer_name:
        raise HTTPException(status_code=400, detail="Customer name is required")

    # Calculate totals from items
    subtotal = 0
    for item in items:
        qty = float(item.get("quantity", 1))
        price = float(item.get("unit_price", 0))
        item["line_total"] = round(qty * price, 2)
        subtotal += item["line_total"]

    if subtotal <= 0:
        raise HTTPException(status_code=400, detail="Invoice total must be positive")

    vat_amount = round(subtotal * 0.075, 2) if vat_enabled else 0
    total_amount = round(subtotal + vat_amount, 2)

    # Auto-generate invoice number
    count = await db.invoices.count_documents({"user_id": user["id"]})
    inv_number = f"INV-{str(count + 1).zfill(3)}"

    invoice = {
        "id": str(uuid.uuid4()),
        "invoice_number": inv_number,
        "user_id": user["id"],
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "items": items,
        "subtotal": subtotal,
        "vat_amount": vat_amount,
        "total_amount": total_amount,
        "vat_enabled": vat_enabled,
        "status": "unpaid",
        "issue_date": datetime.now(timezone.utc).isoformat(),
        "due_date": due_date or (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "paid_date": None,
        "matched_transaction_id": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await db.invoices.insert_one(invoice)
    invoice.pop("_id", None)

    # Update accrued VAT
    if vat_amount > 0:
        await db.vat_liability.update_one(
            {"user_id": user["id"]},
            {"$inc": {"accrued_vat": vat_amount}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )

    return invoice


@router.get("/invoices")
async def get_invoices(status: str = None, user: dict = Depends(get_current_user)):
    query = {"user_id": user["id"]}
    if status:
        query["status"] = status
    invoices = await db.invoices.find(query, {"_id": 0}).sort("created_at", -1).limit(100).to_list(100)
    # Mark overdue
    now = datetime.now(timezone.utc).isoformat()
    for inv in invoices:
        if inv.get("status") == "unpaid" and inv.get("due_date") and inv["due_date"] < now:
            inv["status"] = "overdue"
    return invoices


@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, user: dict = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": invoice_id, "user_id": user["id"]}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.put("/invoices/{invoice_id}/status")
async def update_invoice_status(invoice_id: str, request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    new_status = data.get("status")
    if new_status not in ["unpaid", "paid", "partial", "overdue"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    update = {"status": new_status}
    if new_status == "paid":
        update["paid_date"] = datetime.now(timezone.utc).isoformat()
    await db.invoices.update_one(
        {"id": invoice_id, "user_id": user["id"]},
        {"$set": update}
    )
    return {"message": "Invoice status updated"}


# ========================
# VAT DASHBOARD
# ========================

@router.get("/vat/summary")
async def get_vat_summary(user: dict = Depends(get_current_user)):
    """Real-time VAT micro-dashboard data."""
    user_id = user["id"]

    # Get accrued VAT from invoices
    liability = await db.vat_liability.find_one({"user_id": user_id}, {"_id": 0})
    accrued_vat = liability.get("accrued_vat", 0) if liability else 0

    # Calculate from actual sales transactions
    income_txs = await db.transactions.find(
        {"user_id": user_id, "type": "income"},
        {"_id": 0, "amount": 1}
    ).limit(1000).to_list(1000)

    total_revenue = sum(tx["amount"] for tx in income_txs)
    estimated_vat = round(total_revenue * 0.075, 2)

    # Get tax reserve
    reserve = await db.tax_reserves.find_one({"user_id": user_id}, {"_id": 0})
    tax_reserve = reserve.get("amount", 0) if reserve else 0

    # Unpaid invoices
    unpaid_count = await db.invoices.count_documents({"user_id": user_id, "status": "unpaid"})

    return {
        "total_revenue": total_revenue,
        "estimated_vat_collected": estimated_vat,
        "accrued_vat_from_invoices": accrued_vat,
        "tax_reserve": tax_reserve,
        "recommended_set_aside": estimated_vat,
        "unpaid_invoices": unpaid_count,
        "vat_rate": "7.5%"
    }


# ========================
# JOURNAL ENTRIES (Double-Entry Ledger)
# ========================

@router.post("/journal-entries")
async def create_journal_entry(request: Request, user: dict = Depends(get_current_user)):
    """Create a double-entry journal entry."""
    data = await request.json()

    entry = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "date": data.get("date", datetime.now(timezone.utc).isoformat()),
        "description": data.get("description", ""),
        "debit_account": data.get("debit_account", ""),
        "credit_account": data.get("credit_account", ""),
        "amount": float(data.get("amount", 0)),
        "entry_type": data.get("entry_type", "manual"),
        "source": data.get("source", "manual"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await db.journal_entries.insert_one(entry)
    entry.pop("_id", None)
    return entry


@router.get("/journal-entries")
async def get_journal_entries(user: dict = Depends(get_current_user)):
    return await db.journal_entries.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).sort("date", -1).limit(100).to_list(100)
