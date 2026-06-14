"""Subscription Payments via Flutterwave V4"""
import uuid
import hmac
import hashlib
import logging
import os
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request
from bson import ObjectId

from database import db
from config import SUBSCRIPTION_PRICES
from models import PaymentInitRequest
from utils.auth import get_current_user
from utils.flutterwave import flw_request, is_flutterwave_configured

logger = logging.getLogger(__name__)

router = APIRouter()

FRONTEND_URL = os.environ.get("FRONTEND_URL")
FLW_WEBHOOK_SECRET = os.environ.get("FLW_WEBHOOK_SECRET_HASH", "")


@router.post("/subscription/initialize")
async def initialize_payment(data: PaymentInitRequest, user: dict = Depends(get_current_user)):
    if data.plan not in SUBSCRIPTION_PRICES:
        raise HTTPException(status_code=400, detail="Invalid subscription plan")

    amount = SUBSCRIPTION_PRICES[data.plan] / 100  # Convert kobo to Naira
    tx_ref = f"cfng_sub_{uuid.uuid4().hex[:16]}"
    callback_url = data.callback_url or f"{FRONTEND_URL}/payment-success"

    if not is_flutterwave_configured():
        # Mock mode — direct upgrade
        await db.users.update_one(
            {"_id": ObjectId(user["id"])},
            {"$set": {"subscription_plan": data.plan}}
        )
        return {"mock": True, "upgraded": True, "plan": data.plan}

    try:
        fw_payload = {
            "tx_ref": tx_ref,
            "amount": amount,
            "currency": "NGN",
            "redirect_url": callback_url,
            "payment_options": "card,banktransfer,ussd",
            "customer": {"email": user["email"], "name": user.get("name", "")},
            "customizations": {
                "title": "ClearFile NG",
                "description": f"Subscription — {data.plan.title()} Plan"
            },
            "meta": {"user_id": user["id"], "plan": data.plan, "product": "subscription"}
        }

        response = await flw_request("POST", "/v3/payments", json=fw_payload)
        result = response.json()

        if response.status_code < 400 and result.get("data", {}).get("link"):
            await db.payments.insert_one({
                "user_id": user["id"],
                "reference": tx_ref,
                "plan": data.plan,
                "amount": amount,
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            return {"payment_link": result["data"]["link"], "tx_ref": tx_ref}

        logger.error(f"Flutterwave sub init response: {result}")
        raise HTTPException(status_code=400, detail=result.get("message", "Payment initialization failed"))
    except HTTPException:
        raise
    except Exception as e:
        msg = str(e)
        if "authentication failed" in msg.lower() or "credentials" in msg.lower():
            logger.error(f"Flutterwave auth error: {e}")
            raise HTTPException(status_code=502, detail="Payment gateway authentication failed. Contact admin to verify Flutterwave API credentials.")
        logger.error(f"Flutterwave subscription error: {e}")
        raise HTTPException(status_code=500, detail="Payment service unavailable")


@router.get("/subscription/verify")
async def verify_subscription(transaction_id: str = None, tx_ref: str = None, user: dict = Depends(get_current_user)):
    """Verify subscription payment via Flutterwave."""
    if not is_flutterwave_configured():
        return {"status": "success", "mode": "mock"}

    if not transaction_id:
        raise HTTPException(status_code=400, detail="transaction_id required")

    try:
        response = await flw_request("GET", f"/v3/transactions/{transaction_id}/verify")
        result = response.json()
        data = result.get("data", {})

        if data.get("status") == "successful" and data.get("currency") == "NGN":
            meta = data.get("meta") or {}
            plan = meta.get("plan")
            ref = data.get("tx_ref", tx_ref)

            # Fallback: resolve plan from payment record
            if not plan and ref:
                payment = await db.payments.find_one({"reference": ref})
                plan = payment["plan"] if payment else "starter"

            await db.users.update_one(
                {"_id": ObjectId(user["id"])},
                {"$set": {"subscription_plan": plan}}
            )
            await db.payments.update_one(
                {"reference": ref},
                {"$set": {
                    "status": "success",
                    "transaction_id": transaction_id,
                    "verified_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            logger.info(f"Subscription activated: {user['email']} -> {plan}")
            return {"status": "success", "plan": plan}

        return {"status": "failed", "message": "Payment verification failed"}
    except Exception as e:
        logger.error(f"Flutterwave sub verify error: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")


@router.post("/subscription/webhook")
async def flutterwave_webhook(request: Request):
    """Handle Flutterwave webhook events."""
    secret_hash = FLW_WEBHOOK_SECRET
    signature = request.headers.get("verif-hash", "")

    if secret_hash and signature != secret_hash:
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    event = await request.json()
    event_type = event.get("event")
    data = event.get("data", {})

    if event_type == "charge.completed" and data.get("status") == "successful":
        tx_ref = data.get("tx_ref", "")
        transaction_id = data.get("id")

        if tx_ref.startswith("cfng_sub_"):
            # Subscription payment
            payment = await db.payments.find_one({"reference": tx_ref})
            if payment:
                await db.users.update_one(
                    {"_id": ObjectId(payment["user_id"])},
                    {"$set": {"subscription_plan": payment["plan"]}}
                )
                await db.payments.update_one(
                    {"reference": tx_ref},
                    {"$set": {"status": "success", "transaction_id": transaction_id, "webhook_verified": True}}
                )
                logger.info(f"Webhook: Subscription activated for {tx_ref}")

        elif tx_ref.startswith("cfng_aiguide_"):
            # AI Guide payment
            await db.ai_guide_unlocks.update_one(
                {"reference": tx_ref},
                {"$set": {"status": "active", "transaction_id": transaction_id, "webhook_verified": True}}
            )
            logger.info(f"Webhook: AI Guide unlocked for {tx_ref}")

    return {"status": "ok"}


@router.get("/subscription/plans")
async def get_subscription_plans():
    return {
        "plans": [
            {
                "id": "starter",
                "name": "Starter",
                "price": 2000,
                "price_display": "₦2,000",
                "target": "Freelancers / Simple Income",
                "features": [
                    "Manual income & expense tracking",
                    "Basic tax estimate & filing reminders",
                    "Receipt scanner (Up to 20/month)",
                    "Up to 100 transactions/month"
                ],
                "bank_linking": False
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 4000,
                "price_display": "₦4,000",
                "target": "Power Users & Small Businesses",
                "features": [
                    "Everything in Starter",
                    "Unlimited bank account linking",
                    "Unlimited transactions & AI Auto-categorization",
                    "VAT & WHT tracking",
                    "Full AI Tax Assistant",
                    "1-Click PDF/Excel tax report exports"
                ],
                "bank_linking": True,
                "popular": True
            }
        ],
        "flutterwave_configured": is_flutterwave_configured()
    }
