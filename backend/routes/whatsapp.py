"""WhatsApp Expense Logging - Webhook + NLP Engine"""
import uuid
import os
import re
import logging
import json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional

from database import db
from utils.auth import get_current_user
from utils.tax import calculate_pita, calculate_cita, calculate_vat

logger = logging.getLogger(__name__)

router = APIRouter()

# Nigerian financial text patterns
AMOUNT_PATTERNS = [
    r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:naira|ngn|#)',
    r'(?:N|₦|#)\s*(\d+(?:,\d{3})*(?:\.\d+)?)',
    r'(\d+)k\b',
    r'(\d+(?:,\d{3})*(?:\.\d+)?)',
]

# Category keywords mapping
CATEGORY_KEYWORDS = {
    "Telecommunications": ["mtn", "airtel", "glo", "9mobile", "data", "airtime", "recharge", "top-up", "topup"],
    "Transport": ["uber", "bolt", "taxi", "fuel", "petrol", "diesel", "transport", "bus", "keke", "okada", "danfo"],
    "Utilities": ["nepa", "phcn", "electricity", "light bill", "water bill", "dstv", "gotv", "startimes", "internet", "wifi", "isp"],
    "Rent": ["rent", "house rent", "office rent", "shop rent"],
    "Food": ["food", "lunch", "dinner", "breakfast", "suya", "amala", "rice", "restaurant", "eat"],
    "Equipment": ["laptop", "phone", "computer", "printer", "equipment", "tools", "generator", "inverter"],
    "Marketing": ["ads", "advert", "facebook ads", "google ads", "flyer", "banner", "marketing", "promotion"],
    "Professional Fees": ["lawyer", "accountant", "consultant", "legal", "audit"],
    "Subscriptions": ["netflix", "spotify", "subscription", "saas", "software", "canva", "zoom"],
    "Miscellaneous": []
}

# Tax-deductible categories
DEDUCTIBLE_CATEGORIES = {"Telecommunications", "Transport", "Utilities", "Rent", "Equipment", "Marketing", "Professional Fees", "Subscriptions"}


def parse_amount(text: str) -> Optional[float]:
    """Extract amount from Nigerian financial text."""
    text_lower = text.lower().strip()

    # Check for "k" shorthand (5k = 5000)
    k_match = re.search(r'(\d+(?:\.\d+)?)\s*k\b', text_lower)
    if k_match:
        return float(k_match.group(1)) * 1000

    # Check for explicit currency symbols
    for pattern in AMOUNT_PATTERNS[:-1]:
        match = re.search(pattern, text_lower)
        if match:
            amount_str = match.group(1).replace(',', '')
            return float(amount_str)

    # Fallback: any number
    num_match = re.search(r'(\d+(?:,\d{3})*(?:\.\d+)?)', text_lower)
    if num_match:
        return float(num_match.group(1).replace(',', ''))

    return None


def categorize_text(text: str) -> str:
    """Categorize expense from natural language text."""
    text_lower = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return category
    return "Miscellaneous"


def parse_expense_message(text: str) -> dict:
    """Parse a natural language expense message into structured data."""
    amount = parse_amount(text)
    category = categorize_text(text)
    is_deductible = category in DEDUCTIBLE_CATEGORIES

    return {
        "amount": amount,
        "category": category,
        "is_deductible": is_deductible,
        "original_text": text,
        "description": text.strip()[:200]
    }


@router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    """
    Receive incoming WhatsApp messages via webhook (Twilio/Meta format).
    Parses Nigerian financial text and creates transactions.
    """
    try:
        content_type = request.headers.get("content-type", "")

        if "application/json" in content_type:
            payload = await request.json()
        else:
            # Twilio sends form-encoded
            form = await request.form()
            payload = dict(form)

        # Extract message details (support both Twilio and Meta formats)
        sender = payload.get("From") or payload.get("WaId") or ""
        message_body = payload.get("Body") or ""

        # Meta webhook format
        if not message_body and "entry" in payload:
            try:
                entry = payload["entry"][0]
                changes = entry["changes"][0]
                messages = changes["value"].get("messages", [])
                if messages:
                    message_body = messages[0].get("text", {}).get("body", "")
                    sender = messages[0].get("from", "")
            except (IndexError, KeyError):
                pass

        if not message_body:
            return {"status": "ok", "message": "No message body"}

        # Clean phone number
        phone = re.sub(r'[^\d+]', '', sender).replace("whatsapp:", "")

        # Find user by linked phone
        user = await db.users.find_one({"whatsapp_phone": phone})
        if not user:
            # Try matching without country code
            phone_short = phone[-10:] if len(phone) > 10 else phone
            user = await db.users.find_one({"whatsapp_phone": {"$regex": phone_short}})

        if not user:
            logger.warning(f"WhatsApp message from unlinked number: {phone}")
            return {"status": "ok", "message": "User not found", "reply": "Please link your WhatsApp number in the ClearFile NG app settings first."}

        user_id = str(user["_id"])

        # Parse the expense
        parsed = parse_expense_message(message_body)

        if not parsed["amount"] or parsed["amount"] <= 0:
            return {"status": "ok", "reply": "I couldn't understand the amount. Try: 'Paid 5k for MTN data' or 'Spent N15,000 on fuel'"}

        # Create transaction
        tx_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "amount": parsed["amount"],
            "type": "expense",
            "category": parsed["category"],
            "description": parsed["description"],
            "date": datetime.now(timezone.utc).isoformat(),
            "bank_account_id": None,
            "is_recurring": False,
            "ai_categorized": True,
            "is_business": parsed["is_deductible"],
            "flagged": False,
            "source": "whatsapp",
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        await db.transactions.insert_one(tx_doc)
        tx_doc.pop("_id", None)

        # Calculate updated tax estimate
        business_type = user.get("business_type", "freelancer")
        all_expenses = await db.transactions.find(
            {"user_id": user_id, "type": "expense"},
            {"_id": 0, "amount": 1, "category": 1}
        ).limit(1000).to_list(1000)

        deductible_total = sum(
            tx["amount"] for tx in all_expenses
            if tx.get("category") in DEDUCTIBLE_CATEGORIES
        )

        # Build confirmation reply
        deductible_msg = " Your estimated tax has been reduced." if parsed["is_deductible"] else ""
        reply = f"Done! N{parsed['amount']:,.0f} logged under {parsed['category']}.{deductible_msg}"

        logger.info(f"WhatsApp expense logged: {parsed['amount']} - {parsed['category']} for user {user_id}")

        return {
            "status": "ok",
            "reply": reply,
            "transaction": tx_doc,
            "total_deductible": deductible_total
        }

    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/whatsapp/link")
async def link_whatsapp(request: Request, user: dict = Depends(get_current_user)):
    """Link user's WhatsApp number to their account."""
    data = await request.json()
    phone = data.get("phone", "").strip()

    if not phone:
        raise HTTPException(status_code=400, detail="Phone number required")

    # Normalize phone number
    phone = re.sub(r'[^\d+]', '', phone)
    if not phone.startswith("+"):
        if phone.startswith("0"):
            phone = "+234" + phone[1:]
        elif not phone.startswith("234"):
            phone = "+234" + phone

    from bson import ObjectId
    await db.users.update_one(
        {"_id": ObjectId(user["id"])},
        {"$set": {"whatsapp_phone": phone, "whatsapp_linked": True}}
    )

    return {
        "message": "WhatsApp linked successfully",
        "phone": phone,
        "bot_number": "+2349000000000",
        "wa_link": f"https://wa.me/2349000000000?text=Hi%20ClearFile%20NG!%20Link%20my%20account"
    }


@router.get("/whatsapp/status")
async def get_whatsapp_status(user: dict = Depends(get_current_user)):
    """Check if user has WhatsApp linked."""
    return {
        "linked": user.get("whatsapp_linked", False),
        "phone": user.get("whatsapp_phone", ""),
        "bot_number": "+2349000000000",
        "wa_link": "https://wa.me/2349000000000?text=Hi%20ClearFile%20NG!%20Link%20my%20account"
    }


@router.post("/whatsapp/test-parse")
async def test_parse_message(request: Request, user: dict = Depends(get_current_user)):
    """Test the NLP parsing without creating a transaction. Useful for debugging."""
    data = await request.json()
    text = data.get("text", "")

    if not text:
        raise HTTPException(status_code=400, detail="Text required")

    parsed = parse_expense_message(text)
    return {
        "input": text,
        "parsed": parsed,
        "would_create": parsed["amount"] is not None and parsed["amount"] > 0
    }
