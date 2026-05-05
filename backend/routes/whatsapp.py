"""WhatsApp Expense Logging - Meta Business API Integration
Features:
1. Proactive Tagging: Ask users to categorize unlabeled bank transactions
2. Transaction Memory: Remember categories by receiver account number
3. Subscription Gate: Only Pro plan users can interact with the bot
"""
import uuid
import os
import re
import logging
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import PlainTextResponse
from typing import Optional

from database import db
from utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Meta WhatsApp API config
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "clearfileng_webhook_verify_2024")
WHATSAPP_API_URL = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"

FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://tax-naira.preview.emergentagent.com")

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

DEDUCTIBLE_CATEGORIES = {"Telecommunications", "Transport", "Utilities", "Rent", "Equipment", "Marketing", "Professional Fees", "Subscriptions"}

# Valid categories for user replies
VALID_CATEGORIES = list(CATEGORY_KEYWORDS.keys())


def parse_amount(text: str) -> Optional[float]:
    text_lower = text.lower().strip()
    k_match = re.search(r'(\d+(?:\.\d+)?)\s*k\b', text_lower)
    if k_match:
        return float(k_match.group(1)) * 1000
    for pattern in AMOUNT_PATTERNS[:-1]:
        match = re.search(pattern, text_lower)
        if match:
            return float(match.group(1).replace(',', ''))
    num_match = re.search(r'(\d+(?:,\d{3})*(?:\.\d+)?)', text_lower)
    if num_match:
        return float(num_match.group(1).replace(',', ''))
    return None


def categorize_text(text: str) -> str:
    text_lower = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return category
    return "Miscellaneous"


def parse_expense_message(text: str) -> dict:
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
            if response.status_code == 200:
                logger.info(f"WhatsApp message sent to {to}")
                return True
            else:
                logger.error(f"WhatsApp send failed: {response.json()}")
                return False
    except Exception as e:
        logger.error(f"WhatsApp send error: {e}")
        return False


# ========================
# TRANSACTION MEMORY
# ========================

async def get_category_from_memory(user_id: str, receiver_account: str) -> Optional[str]:
    """Check if we have a remembered category for this receiver account."""
    if not receiver_account:
        return None
    memory = await db.transaction_memory.find_one({
        "user_id": user_id,
        "receiver_account": receiver_account
    })
    return memory.get("category") if memory else None


async def save_category_to_memory(user_id: str, receiver_account: str, category: str):
    """Remember category for a receiver account number."""
    if not receiver_account:
        return
    await db.transaction_memory.update_one(
        {"user_id": user_id, "receiver_account": receiver_account},
        {"$set": {
            "category": category,
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
         "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )


# ========================
# PROACTIVE TAGGING
# ========================

async def ask_for_category(user_id: str, phone: str, transaction_id: str, description: str, amount: float):
    """Send a WhatsApp message asking user to categorize an unlabeled transaction."""
    categories_list = "\n".join(f"{i+1}. {cat}" for i, cat in enumerate(VALID_CATEGORIES[:9]))

    message = (
        f"New transaction detected:\n"
        f"Amount: N{amount:,.0f}\n"
        f"Description: {description}\n\n"
        f"What category is this? Reply with the number:\n{categories_list}\n\n"
        f"Or type the category name."
    )

    # Store pending categorization request
    await db.pending_categorizations.update_one(
        {"user_id": user_id, "transaction_id": transaction_id},
        {"$set": {
            "phone": phone,
            "description": description,
            "amount": amount,
            "created_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )

    await send_whatsapp_message(phone, message)


async def handle_category_reply(user_id: str, phone: str, text: str) -> Optional[dict]:
    """Check if user is replying to a category prompt."""
    pending = await db.pending_categorizations.find_one(
        {"user_id": user_id},
        sort=[("created_at", -1)]
    )
    if not pending:
        return None

    # Parse category from reply
    text_lower = text.lower().strip()
    category = None

    # Check if it's a number reply (1-9)
    if text_lower.isdigit():
        idx = int(text_lower) - 1
        if 0 <= idx < len(VALID_CATEGORIES[:9]):
            category = VALID_CATEGORIES[idx]

    # Check if it matches a category name
    if not category:
        for cat in VALID_CATEGORIES:
            if cat.lower() == text_lower or cat.lower().startswith(text_lower):
                category = cat
                break

    if not category:
        return None

    # Update the transaction
    tx_id = pending["transaction_id"]
    is_deductible = category in DEDUCTIBLE_CATEGORIES

    await db.transactions.update_one(
        {"id": tx_id, "user_id": user_id},
        {"$set": {"category": category, "is_business": is_deductible, "ai_categorized": True}}
    )

    # Save to memory if there's a receiver account
    tx = await db.transactions.find_one({"id": tx_id}, {"_id": 0, "receiver_account": 1})
    if tx and tx.get("receiver_account"):
        await save_category_to_memory(user_id, tx["receiver_account"], category)

    # Remove pending
    await db.pending_categorizations.delete_one({"_id": pending["_id"]})

    badge = " [Tax Deductible]" if is_deductible else ""
    return {"category": category, "is_deductible": is_deductible, "badge": badge, "transaction_id": tx_id}


# ========================
# SUBSCRIPTION GATE
# ========================

def is_pro_user(user: dict) -> bool:
    """Check if user has Pro plan (N4k/month). Accepts 'pro', 'growth', or 'business' as valid."""
    plan = user.get("subscription_plan", "starter")
    return plan in ["pro", "growth", "business"]


# ========================
# WEBHOOK ENDPOINTS
# ========================

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
    Features: Subscription gate, transaction memory, proactive tagging.
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

        phone = re.sub(r'[^\d]', '', sender)

        # Find user by linked phone
        user = await db.users.find_one({"whatsapp_phone": {"$regex": phone[-10:]}})

        if not user:
            await send_whatsapp_message(
                sender,
                f"Welcome to ClearFile NG! Please link your WhatsApp number in the app first.\n\nVisit: {FRONTEND_URL}/settings"
            )
            return {"status": "ok", "message": "User not found"}

        user_id = str(user["_id"])

        # ========== SUBSCRIPTION GATE ==========
        if not is_pro_user(user):
            await send_whatsapp_message(
                sender,
                f"This feature is available on the Pro plan (N4,000/month).\n\n"
                f"Upgrade now to unlock:\n"
                f"• WhatsApp expense logging\n"
                f"• AI auto-categorization\n"
                f"• Unlimited transactions\n\n"
                f"Upgrade here: {FRONTEND_URL}/settings"
            )
            return {"status": "ok", "message": "Free user redirected to upgrade"}

        # ========== HANDLE COMMANDS ==========
        text_lower = message_body.lower().strip()

        if text_lower in ["hi", "hello", "hey", "help"]:
            await send_whatsapp_message(
                sender,
                "Hey! I'm your ClearFile NG expense bot.\n\n"
                "Just text your expenses like:\n"
                "• \"Paid 5k for MTN data\"\n"
                "• \"Spent N15,000 on fuel\"\n"
                "• \"Office rent 200k\"\n\n"
                "Commands:\n"
                "• \"balance\" - Your expense summary\n"
                "• \"memory\" - View saved categories\n\n"
                "I'll auto-flag tax-deductible expenses!"
            )
            return {"status": "ok", "message": "Sent help"}

        if text_lower in ["balance", "summary", "total"]:
            expenses = await db.transactions.find(
                {"user_id": user_id, "type": "expense"},
                {"_id": 0, "amount": 1, "category": 1}
            ).limit(1000).to_list(1000)

            total = sum(tx["amount"] for tx in expenses)
            deductible = sum(tx["amount"] for tx in expenses if tx.get("category") in DEDUCTIBLE_CATEGORIES)

            await send_whatsapp_message(
                sender,
                f"Your ClearFile NG Summary:\n\n"
                f"Total Expenses: N{total:,.0f}\n"
                f"Tax Deductible: N{deductible:,.0f}\n"
                f"Tax Savings: ~N{deductible * 0.2:,.0f}\n\n"
                f"Keep logging to reduce your tax bill!"
            )
            return {"status": "ok", "message": "Sent summary"}

        if text_lower == "memory":
            memories = await db.transaction_memory.find(
                {"user_id": user_id}, {"_id": 0}
            ).sort("updated_at", -1).limit(10).to_list(10)

            if not memories:
                await send_whatsapp_message(sender, "No saved categories yet. As you categorize transactions, I'll remember them for next time!")
            else:
                lines = [f"• {m['receiver_account'][-4:]}** → {m['category']}" for m in memories]
                await send_whatsapp_message(sender, f"Your saved categories:\n\n" + "\n".join(lines))
            return {"status": "ok", "message": "Sent memory list"}

        # ========== CHECK IF REPLYING TO CATEGORY PROMPT ==========
        category_result = await handle_category_reply(user_id, phone, message_body)
        if category_result:
            reply = f"Got it! Categorized as {category_result['category']}.{category_result['badge']}"
            if category_result["is_deductible"]:
                reply += " Your estimated tax has been reduced."
            await send_whatsapp_message(sender, reply)
            return {"status": "ok", "reply": reply, "categorized": True}

        # ========== PARSE EXPENSE ==========
        parsed = parse_expense_message(message_body)

        if not parsed["amount"] or parsed["amount"] <= 0:
            await send_whatsapp_message(
                sender,
                "I couldn't understand the amount. Try:\n"
                "• \"Paid 5k for MTN data\"\n"
                "• \"Spent N15,000 on fuel\"\n"
                "• \"Office rent 200k\""
            )
            return {"status": "ok", "reply": "Could not parse amount"}

        # ========== TRANSACTION MEMORY: Check for known receiver ==========
        # Extract receiver account if mentioned (e.g. "Sent 50k to 0123456789")
        account_match = re.search(r'(?:to|account|acct)\s*[:#]?\s*(\d{10})', message_body.lower())
        receiver_account = account_match.group(1) if account_match else None

        if receiver_account:
            remembered_category = await get_category_from_memory(user_id, receiver_account)
            if remembered_category:
                parsed["category"] = remembered_category
                parsed["is_deductible"] = remembered_category in DEDUCTIBLE_CATEGORIES

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
            "receiver_account": receiver_account,
            "is_recurring": False,
            "ai_categorized": True,
            "is_business": parsed["is_deductible"],
            "flagged": False,
            "source": "whatsapp",
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        await db.transactions.insert_one(tx_doc)
        tx_doc.pop("_id", None)

        # Save to memory if receiver account was provided
        if receiver_account and parsed["category"] != "Miscellaneous":
            await save_category_to_memory(user_id, receiver_account, parsed["category"])

        # Build confirmation
        deductible_msg = " Your estimated tax has been reduced." if parsed["is_deductible"] else ""
        badge = " [Tax Deductible]" if parsed["is_deductible"] else ""
        memory_msg = f" (Remembered for acct ***{receiver_account[-4:]})" if receiver_account else ""
        reply = f"Done! N{parsed['amount']:,.0f} logged under {parsed['category']}.{badge}{memory_msg}{deductible_msg}"

        await send_whatsapp_message(sender, reply)
        logger.info(f"WhatsApp expense: N{parsed['amount']:,.0f} - {parsed['category']} for {user_id}")

        return {"status": "ok", "reply": reply, "transaction_id": tx_doc["id"]}

    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        return {"status": "error", "message": str(e)}


# ========================
# PROACTIVE TAGGING TRIGGER (called by banking sync)
# ========================

@router.post("/whatsapp/proactive-tag")
async def trigger_proactive_tag(request: Request):
    """
    Called internally when a bank transaction syncs without a clear label.
    Sends WhatsApp message asking user to categorize it.
    """
    data = await request.json()
    user_id = data.get("user_id")
    transaction_id = data.get("transaction_id")
    description = data.get("description", "Unknown transaction")
    amount = data.get("amount", 0)
    receiver_account = data.get("receiver_account")

    if not user_id or not transaction_id:
        raise HTTPException(status_code=400, detail="user_id and transaction_id required")

    user = await db.users.find_one({"_id": __import__('bson').ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Only for Pro users
    if not is_pro_user(user):
        return {"status": "skipped", "reason": "User not on Pro plan"}

    phone = user.get("whatsapp_phone", "")
    if not phone:
        return {"status": "skipped", "reason": "No WhatsApp linked"}

    # Check transaction memory first
    if receiver_account:
        remembered = await get_category_from_memory(user_id, receiver_account)
        if remembered:
            # Auto-label based on memory
            is_deductible = remembered in DEDUCTIBLE_CATEGORIES
            await db.transactions.update_one(
                {"id": transaction_id, "user_id": user_id},
                {"$set": {"category": remembered, "is_business": is_deductible, "ai_categorized": True}}
            )
            await send_whatsapp_message(
                phone.replace("+", ""),
                f"Auto-labeled: N{amount:,.0f} to ***{receiver_account[-4:]} → {remembered}{' [Tax Deductible]' if is_deductible else ''}"
            )
            return {"status": "ok", "auto_labeled": True, "category": remembered}

    # No memory match — ask user
    await ask_for_category(user_id, phone.replace("+", ""), transaction_id, description, amount)
    return {"status": "ok", "asked_user": True}


# ========================
# USER-FACING ENDPOINTS
# ========================

@router.post("/whatsapp/link")
async def link_whatsapp(request: Request, user: dict = Depends(get_current_user)):
    """Link user's WhatsApp number to their account."""
    data = await request.json()
    phone = data.get("phone", "").strip()

    if not phone:
        raise HTTPException(status_code=400, detail="Phone number required")

    # Subscription gate check
    if not is_pro_user(user):
        raise HTTPException(status_code=403, detail="WhatsApp bot requires Pro plan (N4,000/month). Upgrade in Settings.")

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

    await send_whatsapp_message(
        phone.replace("+", ""),
        "Your ClearFile NG account is linked!\n\n"
        "Log expenses by texting:\n"
        "• \"Paid 5k for MTN data\"\n"
        "• \"Sent 50k to 0123456789 for rent\"\n\n"
        "I'll remember who you pay and auto-label next time!\n\n"
        "Type \"help\" for all commands."
    )

    return {
        "message": "WhatsApp linked successfully",
        "phone": phone,
        "bot_number": WHATSAPP_PHONE_NUMBER_ID,
        "wa_link": f"https://wa.me/{WHATSAPP_PHONE_NUMBER_ID}?text=Hi%20ClearFile%20NG!%20Link%20my%20account"
    }


@router.get("/whatsapp/status")
async def get_whatsapp_status(user: dict = Depends(get_current_user)):
    """Check WhatsApp link status."""
    return {
        "linked": user.get("whatsapp_linked", False),
        "phone": user.get("whatsapp_phone", ""),
        "bot_number": WHATSAPP_PHONE_NUMBER_ID,
        "wa_link": f"https://wa.me/{WHATSAPP_PHONE_NUMBER_ID}?text=Hi%20ClearFile%20NG!%20Link%20my%20account",
        "is_pro": is_pro_user(user)
    }


@router.get("/whatsapp/memory")
async def get_transaction_memory(user: dict = Depends(get_current_user)):
    """Get user's saved category memory mappings."""
    memories = await db.transaction_memory.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).sort("updated_at", -1).limit(50).to_list(50)
    return {"memories": memories, "count": len(memories)}


@router.delete("/whatsapp/memory/{receiver_account}")
async def delete_memory(receiver_account: str, user: dict = Depends(get_current_user)):
    """Delete a category memory mapping."""
    result = await db.transaction_memory.delete_one({
        "user_id": user["id"],
        "receiver_account": receiver_account
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"message": "Memory deleted"}


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
