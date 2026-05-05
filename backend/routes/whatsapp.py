"""WhatsApp Expense Logging - Meta Business API Integration"""
import uuid
import os
import re
import logging
import json
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import PlainTextResponse
from typing import Optional

from database import db
from utils.auth import get_current_user
from utils.tax import calculate_pita, calculate_cita, calculate_vat

logger = logging.getLogger(__name__)

router = APIRouter()

# Meta WhatsApp API config
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "clearfileng_webhook_verify_2024")
WHATSAPP_API_URL = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"

# Nigerian financial text patterns
AMOUNT_PATTERNS = [
    r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:naira|ngn|#)',
    r'(?:N|₦|#)\s*(\d+(?:,\d{3})*(?:\.\d+)?)',
    r'(\d+(?:\.\d+)?)\s*k\b',
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


async def send_whatsapp_message(to: str, text: str):
    """Send a WhatsApp message via Meta API."""
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.warning("WhatsApp API not configured, skipping message send")
        return False

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                WHATSAPP_API_URL,
                headers={
                    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": to,
                    "type": "text",
                    "text": {"body": text}
                },
                timeout=30.0
            )
            result = response.json()
            if response.status_code == 200:
                logger.info(f"WhatsApp message sent to {to}")
                return True
            else:
                logger.error(f"WhatsApp send failed: {result}")
                return False
    except Exception as e:
        logger.error(f"WhatsApp send error: {e}")
        return False


@router.get("/whatsapp/webhook")
async def verify_webhook(request: Request):
    """Meta webhook verification (GET request)."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified successfully")
        return PlainTextResponse(content=challenge, status_code=200)

    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    """
    Receive incoming WhatsApp messages via Meta webhook.
    Parses Nigerian financial text and creates transactions.
    """
    try:
        payload = await request.json()

        # Extract message from Meta webhook format
        message_body = ""
        sender = ""

        if "entry" in payload:
            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    for msg in messages:
                        if msg.get("type") == "text":
                            message_body = msg["text"]["body"]
                            sender = msg["from"]
                            break
                    if message_body:
                        break
                if message_body:
                    break

        if not message_body:
            return {"status": "ok", "message": "No text message"}

        # Clean phone number
        phone = re.sub(r'[^\d]', '', sender)

        # Find user by linked phone
        user = await db.users.find_one({"whatsapp_phone": {"$regex": phone[-10:]}})

        if not user:
            # Send back a message asking them to link
            await send_whatsapp_message(
                sender,
                "Welcome to ClearFile NG! Please link your WhatsApp number in the app settings first.\n\nVisit: https://tax-naira.preview.emergentagent.com/settings"
            )
            return {"status": "ok", "message": "User not found, sent link instructions"}

        user_id = str(user["_id"])

        # Check for commands
        text_lower = message_body.lower().strip()
        if text_lower in ["hi", "hello", "hey", "help"]:
            await send_whatsapp_message(
                sender,
                "Hey! I'm your ClearFile NG expense bot.\n\nJust text your expenses like:\n• \"Paid 5k for MTN data\"\n• \"Spent N15,000 on fuel\"\n• \"Office rent 200k\"\n\nI'll log them automatically and flag tax-deductible ones!"
            )
            return {"status": "ok", "message": "Sent help message"}

        if text_lower in ["balance", "summary", "total"]:
            # Send a quick summary
            expenses = await db.transactions.find(
                {"user_id": user_id, "type": "expense"},
                {"_id": 0, "amount": 1, "category": 1}
            ).limit(1000).to_list(1000)

            total = sum(tx["amount"] for tx in expenses)
            deductible = sum(tx["amount"] for tx in expenses if tx.get("category") in DEDUCTIBLE_CATEGORIES)

            await send_whatsapp_message(
                sender,
                f"Your ClearFile NG Summary:\n\nTotal Expenses: N{total:,.0f}\nTax Deductible: N{deductible:,.0f}\nTax Savings: ~N{deductible * 0.2:,.0f}\n\nKeep logging to reduce your tax bill!"
            )
            return {"status": "ok", "message": "Sent summary"}

        # Parse the expense
        parsed = parse_expense_message(message_body)

        if not parsed["amount"] or parsed["amount"] <= 0:
            await send_whatsapp_message(
                sender,
                "I couldn't understand the amount. Try:\n• \"Paid 5k for MTN data\"\n• \"Spent N15,000 on fuel\"\n• \"Office rent 200k\""
            )
            return {"status": "ok", "reply": "Could not parse amount"}

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

        # Build and send confirmation
        deductible_msg = " Your estimated tax has been reduced." if parsed["is_deductible"] else ""
        badge = " [Tax Deductible]" if parsed["is_deductible"] else ""
        reply = f"Done! N{parsed['amount']:,.0f} logged under {parsed['category']}.{badge}{deductible_msg}"

        await send_whatsapp_message(sender, reply)

        logger.info(f"WhatsApp expense logged: N{parsed['amount']:,.0f} - {parsed['category']} for user {user_id}")

        return {
            "status": "ok",
            "reply": reply,
            "transaction_id": tx_doc["id"]
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

    # Send welcome message
    await send_whatsapp_message(
        phone.replace("+", ""),
        "Your ClearFile NG account is linked! You can now log expenses by texting here.\n\nTry: \"Paid 5k for MTN data\"\n\nType \"help\" for more commands."
    )

    return {
        "message": "WhatsApp linked successfully",
        "phone": phone,
        "bot_number": WHATSAPP_PHONE_NUMBER_ID,
        "wa_link": f"https://wa.me/{WHATSAPP_PHONE_NUMBER_ID}?text=Hi%20ClearFile%20NG!%20Link%20my%20account"
    }


@router.get("/whatsapp/status")
async def get_whatsapp_status(user: dict = Depends(get_current_user)):
    """Check if user has WhatsApp linked."""
    return {
        "linked": user.get("whatsapp_linked", False),
        "phone": user.get("whatsapp_phone", ""),
        "bot_number": WHATSAPP_PHONE_NUMBER_ID,
        "wa_link": f"https://wa.me/{WHATSAPP_PHONE_NUMBER_ID}?text=Hi%20ClearFile%20NG!%20Link%20my%20account"
    }


@router.post("/whatsapp/test-parse")
async def test_parse_message(request: Request, user: dict = Depends(get_current_user)):
    """Test the NLP parsing without creating a transaction."""
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
