import uuid
import hmac
import hashlib
import logging
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request
from bson import ObjectId

from database import db
from config import PAYSTACK_SECRET_KEY, PAYSTACK_PUBLIC_KEY, SUBSCRIPTION_PRICES
from models import PaymentInitRequest
from utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/subscription/initialize")
async def initialize_payment(data: PaymentInitRequest, user: dict = Depends(get_current_user)):
    if data.plan not in SUBSCRIPTION_PRICES:
        raise HTTPException(status_code=400, detail="Invalid subscription plan")

    amount_kobo = SUBSCRIPTION_PRICES[data.plan]
    reference = f"nairatrack_{uuid.uuid4().hex[:16]}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.paystack.co/transaction/initialize",
                headers={
                    "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "email": user["email"],
                    "amount": amount_kobo,
                    "reference": reference,
                    "callback_url": data.callback_url,
                    "metadata": {
                        "user_id": user["id"],
                        "plan": data.plan,
                        "custom_fields": [
                            {"display_name": "Plan", "variable_name": "plan", "value": data.plan},
                            {"display_name": "User", "variable_name": "user_email", "value": user["email"]}
                        ]
                    }
                },
                timeout=30.0
            )
            result = response.json()

        if result.get("status"):
            await db.payments.insert_one({
                "user_id": user["id"],
                "reference": reference,
                "plan": data.plan,
                "amount": amount_kobo,
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat()
            })

            return {
                "authorization_url": result["data"]["authorization_url"],
                "reference": result["data"]["reference"],
                "access_code": result["data"]["access_code"]
            }

        raise HTTPException(status_code=400, detail=result.get("message", "Payment initialization failed"))
    except httpx.HTTPError as e:
        logger.error(f"Paystack error: {e}")
        raise HTTPException(status_code=500, detail="Payment service unavailable")


@router.get("/subscription/verify/{reference}")
async def verify_payment(reference: str, user: dict = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.paystack.co/transaction/verify/{reference}",
                headers={"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"},
                timeout=30.0
            )
            result = response.json()

        if result.get("status") and result["data"]["status"] == "success":
            payment = await db.payments.find_one({"reference": reference})
            plan = payment["plan"] if payment else result["data"]["metadata"].get("plan", "starter")

            await db.users.update_one(
                {"_id": ObjectId(user["id"])},
                {"$set": {"subscription_plan": plan}}
            )
            await db.payments.update_one(
                {"reference": reference},
                {"$set": {"status": "success", "verified_at": datetime.now(timezone.utc).isoformat()}}
            )
            logger.info(f"Subscription activated: {user['email']} -> {plan}")
            return {"status": "success", "plan": plan, "data": result["data"]}

        return {"status": "failed", "message": result.get("message", "Payment verification failed")}
    except httpx.HTTPError as e:
        logger.error(f"Paystack verify error: {e}")
        raise HTTPException(status_code=500, detail="Payment verification failed")


@router.post("/subscription/webhook")
async def paystack_webhook(request: Request):
    signature = request.headers.get("x-paystack-signature")
    body = await request.body()

    if PAYSTACK_SECRET_KEY:
        computed_signature = hmac.new(
            PAYSTACK_SECRET_KEY.encode('utf-8'),
            body,
            hashlib.sha512
        ).hexdigest()
        if signature and not hmac.compare_digest(computed_signature, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

    event = await request.json()
    event_type = event.get("event")

    if event_type == "charge.success":
        data = event["data"]
        reference = data["reference"]
        payment = await db.payments.find_one({"reference": reference})
        if payment:
            await db.users.update_one(
                {"_id": ObjectId(payment["user_id"])},
                {"$set": {"subscription_plan": payment["plan"]}}
            )
            await db.payments.update_one(
                {"reference": reference},
                {"$set": {"status": "success", "webhook_verified": True}}
            )
            logger.info(f"Webhook: Subscription activated via webhook for {reference}")

    return {"status": "ok"}


@router.get("/subscription/plans")
async def get_subscription_plans():
    return {
        "plans": [
            {
                "id": "starter",
                "name": "Starter",
                "price": 2000,
                "price_display": "N2,000",
                "features": [
                    "Manual expense tracking",
                    "Basic tax estimate",
                    "Filing reminders",
                    "Receipt scanner (10/month)",
                    "Up to 50 transactions/month"
                ],
                "bank_linking": False
            },
            {
                "id": "growth",
                "name": "Growth",
                "price": 4000,
                "price_display": "N4,000",
                "features": [
                    "Everything in Starter",
                    "Bank account linking (2 accounts)",
                    "Auto-categorization",
                    "AI spending organizer",
                    "VAT & WHT tracking",
                    "Up to 300 transactions/month"
                ],
                "bank_linking": True,
                "popular": True
            },
            {
                "id": "business",
                "name": "Business",
                "price": 6000,
                "price_display": "N6,000",
                "features": [
                    "Everything in Growth",
                    "Unlimited bank accounts",
                    "Unlimited transactions",
                    "PDF/Excel export",
                    "Multi-user access",
                    "Priority support",
                    "Full AI tax assistant"
                ],
                "bank_linking": True
            }
        ],
        "paystack_public_key": PAYSTACK_PUBLIC_KEY
    }
