"""WhatsApp Conversational AI Backend for ClearFile NG
MSME Transaction Guardrails:
1. Reverse Co-mingling — Classify personal vs business from Mono bank feed
2. Auto-Routing Owner Contributions — Journal entries from natural language
3. Smart Invoice & Payment Reconciliation — Prevent double-counting
4. Real-Time VAT & Tax Micro-Dashboard — Weekly digest, on-demand summary
5. Subscription Gate — Pro plan only
6. Transaction Memory — Remember categories by receiver account
"""
import uuid
import os
import re
import json
import logging
import httpx
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import PlainTextResponse
from typing import Optional

from database import db
from utils.auth import get_current_user
from utils.tax import calculate_pit, calculate_cit
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

router = APIRouter()

WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "clearfileng_webhook_verify_2024")
WHATSAPP_APP_SECRET = os.environ.get("WHATSAPP_APP_SECRET", "")
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")

CLEARFILE_AI_SYSTEM_PROMPT = """You are ClearFile, a bookkeeping assistant for Nigerian small business owners. You work through WhatsApp. You understand Nigerian Pidgin English and Standard English equally. You never use accounting words like debit, credit, ledger, journal entry, or accrual. You keep every message short and clear. You only ask one question per message. You never send more than 3 messages in a row without waiting for a reply.

You understand these Nigerian business phrases automatically:
- 'my customer just paid' or 'my buyer settle me' or 'they send am' = Sales Revenue
- 'I collected advance' or 'customer drop something' = Customer Deposit
- 'I buy fuel for generator' or 'I buy gen fuel' or 'I buy diesel' = Utilities - Generator
- 'I pay transport' or 'I take keke' or 'I enter uber' or 'I take okada' = Travel and Transport
- 'I pay my boy' or 'I settle my staff' or 'I pay salary' = Staff Wages
- 'I buy goods' or 'I restock' or 'I buy market' or 'I buy materials' = Cost of Goods
- 'I pay for space' or 'I settle oga landlord' or 'I pay rent' = Rent
- 'I buy data' or 'I recharge' = Communication
- 'I send to my wife' or 'I send home' or 'I dash family' = Personal expense - Owner's Draw
- 'I put money inside the business' or 'I fund the business' = Owner Capital Injection
- 'I borrow from business' = Owner's Draw / Loan from Business

If the user description is unclear after 2 exchanges, classify as Uncategorized and tell the user to edit it later.

Respond ONLY with a valid JSON object. No other text. The JSON must have these fields: category (string), confidence (number between 0 and 1), isPersonalRisk (boolean — true if this might be a personal expense), requiresClarification (boolean), clarificationQuestion (string or null), shortDescription (plain English description of what this transaction is for)"""


async def classify_with_ai(description: str, amount: float = 0, tx_type: str = "expense") -> dict:
    """Use Claude Opus 4.8 to classify a transaction."""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"clearfile_classify_{uuid.uuid4().hex[:8]}",
            system_message=CLEARFILE_AI_SYSTEM_PROMPT
        ).with_model("anthropic", "claude-opus-4-8")

        prompt = f"Transaction: {tx_type.upper()} of ₦{amount:,.0f}. Description: \"{description}\""
        response = await chat.send_message(UserMessage(text=prompt))
        text = response.text.strip()

        # Extract JSON from response
        if text.startswith("{"):
            return json.loads(text)
        # Try to find JSON in response
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return {"category": "Uncategorized", "confidence": 0, "isPersonalRisk": False, "requiresClarification": True, "clarificationQuestion": "What was this payment for?", "shortDescription": description}
    except Exception as e:
        logger.error(f"AI classification error: {e}")
        return {"category": "Uncategorized", "confidence": 0, "isPersonalRisk": False, "requiresClarification": True, "clarificationQuestion": "What was this payment for?", "shortDescription": description}
WHATSAPP_API_URL = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
FRONTEND_URL = os.environ.get("FRONTEND_URL")

# ========================
# CONSTANTS
# ========================

CATEGORY_KEYWORDS = {
    "Telecommunications": ["mtn", "airtel", "glo", "9mobile", "data", "airtime", "recharge", "topup"],
    "Transport": ["uber", "bolt", "taxi", "fuel", "petrol", "diesel", "transport", "bus", "keke", "okada"],
    "Utilities": ["nepa", "phcn", "electricity", "light bill", "water bill", "dstv", "gotv", "internet", "wifi"],
    "Rent": ["rent", "house rent", "office rent", "shop rent"],
    "Food": ["food", "lunch", "dinner", "breakfast", "suya", "restaurant", "eat"],
    "Equipment": ["laptop", "phone", "computer", "printer", "equipment", "generator", "inverter"],
    "Marketing": ["ads", "advert", "facebook ads", "google ads", "marketing", "promotion"],
    "Professional Fees": ["lawyer", "accountant", "consultant", "legal", "audit"],
    "Subscriptions": ["netflix", "spotify", "subscription", "software", "canva", "zoom"],
}

PERSONAL_INDICATORS = [
    "netflix", "spotify", "showmax", "amazon prime", "dstv", "gotv", "startimes",
    "bet9ja", "betway", "sportybet", "nairabet", "1xbet",
    "shoprite", "spar", "game", "pep", "primark",
    "cinema", "gym", "spa", "salon", "barber",
    "school fees", "tuition", "church", "tithe", "offering"
]

DEDUCTIBLE_CATEGORIES = {"Telecommunications", "Transport", "Utilities", "Rent", "Equipment", "Marketing", "Professional Fees", "Subscriptions"}

VALID_CATEGORIES = list(CATEGORY_KEYWORDS.keys()) + ["Miscellaneous"]

# Conversation states
STATE_IDLE = "idle"
STATE_AWAITING_CATEGORY = "awaiting_category"
STATE_AWAITING_COMINGLE_REPLY = "awaiting_comingle"
STATE_AWAITING_OWNER_CONTRIB = "awaiting_owner_contrib"
STATE_AWAITING_INVOICE_MATCH = "awaiting_invoice_match"


# ========================
# HELPERS
# ========================

def parse_amount(text: str) -> Optional[float]:
    text_lower = text.lower().strip()
    k_match = re.search(r'(\d+(?:\.\d+)?)\s*k\b', text_lower)
    if k_match:
        return float(k_match.group(1)) * 1000
    for pattern in [r'(?:N|₦|#)\s*(\d+(?:,\d{3})*(?:\.\d+)?)', r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:naira|ngn)']:
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


def is_likely_personal(description: str) -> bool:
    desc_lower = description.lower()
    return any(indicator in desc_lower for indicator in PERSONAL_INDICATORS)


def is_pro_user(user: dict) -> bool:
    return user.get("subscription_plan", "starter") in ["pro", "growth", "business"]


async def send_whatsapp_message(to: str, text: str):
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.warning(f"WA mock send to {to}: {text[:100]}")
        return True
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                WHATSAPP_API_URL,
                headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"},
                json={"messaging_product": "whatsapp", "recipient_type": "individual", "to": to, "type": "text", "text": {"body": text}},
                timeout=30.0
            )
            return response.status_code == 200
    except Exception as e:
        logger.error(f"WA send error: {e}")
        return False


async def send_whatsapp_buttons(to: str, body: str, buttons: list):
    """Send interactive button message."""
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.warning(f"WA mock buttons to {to}: {body[:80]}")
        return True
    try:
        btn_payload = [{"type": "reply", "reply": {"id": b["id"], "title": b["title"][:20]}} for b in buttons[:3]]
        async with httpx.AsyncClient() as client:
            response = await client.post(
                WHATSAPP_API_URL,
                headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"},
                json={
                    "messaging_product": "whatsapp", "recipient_type": "individual", "to": to,
                    "type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": body},
                        "action": {"buttons": btn_payload}
                    }
                },
                timeout=30.0
            )
            return response.status_code == 200
    except Exception as e:
        logger.error(f"WA buttons error: {e}")
        # Fallback to text
        btn_text = "\n".join(f"• Reply \"{b['title']}\"" for b in buttons)
        return await send_whatsapp_message(to, f"{body}\n\n{btn_text}")


async def get_user_state(user_id: str) -> dict:
    state = await db.wa_conversation_state.find_one({"user_id": user_id})
    if not state:
        return {"state": STATE_IDLE, "data": {}}
    return {"state": state.get("state", STATE_IDLE), "data": state.get("data", {})}


async def set_user_state(user_id: str, state: str, data: dict = None):
    await db.wa_conversation_state.update_one(
        {"user_id": user_id},
        {"$set": {"state": state, "data": data or {}, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )


async def clear_user_state(user_id: str):
    await db.wa_conversation_state.update_one(
        {"user_id": user_id},
        {"$set": {"state": STATE_IDLE, "data": {}}},
        upsert=True
    )


# ========================
# TRANSACTION MEMORY
# ========================

async def get_category_from_memory(user_id: str, receiver_account: str) -> Optional[str]:
    if not receiver_account:
        return None
    memory = await db.transaction_memory.find_one({"user_id": user_id, "counterparty_account": receiver_account})
    return memory.get("category") if memory else None


async def save_category_to_memory(user_id: str, receiver_account: str, category: str):
    if not receiver_account:
        return
    await db.transaction_memory.update_one(
        {"user_id": user_id, "counterparty_account": receiver_account},
        {"$set": {"category": category, "updated_at": datetime.now(timezone.utc).isoformat()},
         "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )


# ========================
# 1. REVERSE CO-MINGLING
# ========================

async def handle_comingle_check(user_id: str, phone: str, tx_data: dict):
    """Check if a bank transaction is personal or business and ask the user."""
    description = tx_data.get("description", "")
    amount = tx_data.get("amount", 0)
    merchant = tx_data.get("merchant", description)
    date = tx_data.get("date", datetime.now(timezone.utc).strftime("%b %d"))
    tx_id = tx_data.get("id", str(uuid.uuid4()))

    if is_likely_personal(description):
        # Flag as ambiguous — ask user
        await set_user_state(user_id, STATE_AWAITING_COMINGLE_REPLY, {
            "transaction_id": tx_id, "amount": amount, "description": description
        })

        body = f"Hey! I noticed a debit of ₦{amount:,.0f} at {merchant} on {date}. Was this a personal expense or a business expense?"
        await send_whatsapp_buttons(phone, body, [
            {"id": "personal_expense", "title": "Personal Expense"},
            {"id": "business_expense", "title": "Business Expense"}
        ])
        return True
    return False


async def process_comingle_reply(user_id: str, phone: str, reply: str, state_data: dict):
    """Process the user's reply to a co-mingling question."""
    tx_id = state_data.get("transaction_id")
    amount = state_data.get("amount", 0)
    description = state_data.get("description", "")
    reply_lower = reply.lower().strip()

    if "personal" in reply_lower or reply_lower == "personal_expense":
        # Map to Owner's Draw — exclude from business P&L
        await db.transactions.update_one(
            {"id": tx_id, "user_id": user_id},
            {"$set": {"category": "Owner's Draw", "is_business": False, "is_personal": True, "ai_categorized": True}}
        )
        # Create journal entry: Debit Owner's Draw, Credit Cash
        await db.journal_entries.insert_one({
            "id": str(uuid.uuid4()), "user_id": user_id,
            "description": f"Personal expense: {description}",
            "debit_account": "Owner's Draw", "credit_account": "Cash/Bank",
            "amount": amount, "entry_type": "auto_comingle",
            "source": "whatsapp", "created_at": datetime.now(timezone.utc).isoformat()
        })
        await send_whatsapp_message(phone, f"Got it! ₦{amount:,.0f} marked as Personal (Owner's Draw). It won't affect your business profit calculations.")
    elif "business" in reply_lower or reply_lower == "business_expense":
        # Ask for category
        await set_user_state(user_id, STATE_AWAITING_CATEGORY, {"transaction_id": tx_id})
        cats = "\n".join(f"{i+1}. {c}" for i, c in enumerate(VALID_CATEGORIES[:9]))
        await send_whatsapp_message(phone, f"What category? Reply with the number:\n{cats}")
        return
    else:
        await send_whatsapp_message(phone, "Please reply with \"Personal Expense\" or \"Business Expense\".")
        return

    await clear_user_state(user_id)


# ========================
# 2. AUTO-ROUTING OWNER CONTRIBUTIONS
# ========================

async def handle_owner_contribution(user_id: str, phone: str, amount: float, reply: str):
    """Route owner contributions with correct double-entry bookkeeping."""
    reply_lower = reply.lower().strip()

    if "funded" in reply_lower or reply_lower == "i_funded_business":
        # Owner injected capital: Credit Owner's Equity, Debit Cash
        await db.journal_entries.insert_one({
            "id": str(uuid.uuid4()), "user_id": user_id,
            "description": f"Owner capital injection: ₦{amount:,.0f}",
            "debit_account": "Cash/Bank", "credit_account": "Owner's Equity/Capital",
            "amount": amount, "entry_type": "owner_contribution",
            "source": "whatsapp", "created_at": datetime.now(timezone.utc).isoformat()
        })
        await db.transactions.insert_one({
            "id": str(uuid.uuid4()), "user_id": user_id,
            "amount": amount, "type": "income", "category": "Capital Injection",
            "description": "Owner funded the business", "date": datetime.now(timezone.utc).isoformat(),
            "is_business": True, "is_owner_equity": True, "ai_categorized": True,
            "source": "whatsapp", "created_at": datetime.now(timezone.utc).isoformat()
        })
        await send_whatsapp_message(phone, f"Recorded! ₦{amount:,.0f} logged as Owner's Capital Injection. Your Cash account is debited, Owner's Equity credited.")

    elif "paid" in reply_lower or "back" in reply_lower or reply_lower == "business_paid_me":
        # Business repaying owner: Debit Owner's Draw/Loan Payable, Credit Cash
        await db.journal_entries.insert_one({
            "id": str(uuid.uuid4()), "user_id": user_id,
            "description": f"Business repaid owner: ₦{amount:,.0f}",
            "debit_account": "Owner's Draw/Loan Payable", "credit_account": "Cash/Bank",
            "amount": amount, "entry_type": "owner_repayment",
            "source": "whatsapp", "created_at": datetime.now(timezone.utc).isoformat()
        })
        await db.transactions.insert_one({
            "id": str(uuid.uuid4()), "user_id": user_id,
            "amount": amount, "type": "expense", "category": "Owner's Draw",
            "description": "Business repaid owner loan", "date": datetime.now(timezone.utc).isoformat(),
            "is_business": True, "is_owner_draw": True, "ai_categorized": True,
            "source": "whatsapp", "created_at": datetime.now(timezone.utc).isoformat()
        })
        await send_whatsapp_message(phone, f"Recorded! ₦{amount:,.0f} logged as Owner Repayment. Loan Payable debited, Cash credited.")
    else:
        await send_whatsapp_message(phone, "Please reply:\n• \"I funded the business\"\n• \"Business paid me back\"")
        return

    await clear_user_state(user_id)


# ========================
# 3. SMART INVOICE RECONCILIATION
# ========================

async def attempt_invoice_reconciliation(user_id: str, phone: str, amount: float, tx_id: str):
    """Try to match an incoming payment to unpaid invoices."""
    # Find invoices within ±2% of the amount
    lower = amount * 0.98
    upper = amount * 1.02

    matching_invoices = await db.invoices.find({
        "user_id": user_id,
        "status": "unpaid",
        "total": {"$gte": lower, "$lte": upper}
    }, {"_id": 0}).limit(5).to_list(5)

    if len(matching_invoices) == 1:
        # Single match — auto-reconcile
        inv = matching_invoices[0]
        await db.invoices.update_one(
            {"id": inv["id"]},
            {"$set": {"status": "paid", "matched_transaction_id": tx_id, "paid_at": datetime.now(timezone.utc).isoformat()}}
        )
        await send_whatsapp_message(
            phone,
            f"Invoice {inv['invoice_number']} for {inv.get('customer_name', 'customer')} has been automatically marked as PAID via your bank feed. ₦{amount:,.0f} matched successfully."
        )
        return True

    elif len(matching_invoices) > 1:
        # Multiple matches — ask user
        options = "\n".join(
            f"{i+1}. {inv['invoice_number']} — {inv.get('customer_name', 'N/A')} — ₦{inv['total']:,.0f}"
            for i, inv in enumerate(matching_invoices)
        )
        await set_user_state(user_id, STATE_AWAITING_INVOICE_MATCH, {
            "transaction_id": tx_id, "amount": amount,
            "invoice_ids": [inv["id"] for inv in matching_invoices]
        })
        await send_whatsapp_message(
            phone,
            f"I found {len(matching_invoices)} invoices matching ₦{amount:,.0f}. Which one was paid?\n\n{options}\n\nReply with the number."
        )
        return True

    return False


async def process_invoice_match_reply(user_id: str, phone: str, reply: str, state_data: dict):
    """Process user's invoice selection."""
    invoice_ids = state_data.get("invoice_ids", [])
    tx_id = state_data.get("transaction_id")
    amount = state_data.get("amount", 0)

    try:
        idx = int(reply.strip()) - 1
        if 0 <= idx < len(invoice_ids):
            inv_id = invoice_ids[idx]
            inv = await db.invoices.find_one({"id": inv_id}, {"_id": 0})
            if inv:
                await db.invoices.update_one(
                    {"id": inv_id},
                    {"$set": {"status": "paid", "matched_transaction_id": tx_id, "paid_at": datetime.now(timezone.utc).isoformat()}}
                )
                await send_whatsapp_message(phone, f"Invoice {inv['invoice_number']} marked as PAID. ₦{amount:,.0f} matched.")
                await clear_user_state(user_id)
                return
    except (ValueError, IndexError):
        pass

    await send_whatsapp_message(phone, "Please reply with the invoice number (1, 2, 3, etc.)")


# ========================
# 4. VAT & TAX MICRO-DASHBOARD
# ========================

async def send_tax_summary(user_id: str, phone: str):
    """Send real-time VAT & tax summary via WhatsApp."""
    income_txs = await db.transactions.find(
        {"user_id": user_id, "type": "income", "is_personal": {"$ne": True}},
        {"_id": 0, "amount": 1}
    ).limit(1000).to_list(1000)

    expense_txs = await db.transactions.find(
        {"user_id": user_id, "type": "expense", "is_personal": {"$ne": True}},
        {"_id": 0, "amount": 1, "category": 1}
    ).limit(1000).to_list(1000)

    total_revenue = sum(tx["amount"] for tx in income_txs)
    total_expenses = sum(tx["amount"] for tx in expense_txs)
    vat_collected = round(total_revenue * 0.075, 2)

    deductible_cats = {"Rent", "Utilities", "Professional Fees", "Marketing", "Equipment", "Subscriptions", "Transport", "Telecommunications"}
    deductible = sum(tx["amount"] for tx in expense_txs if tx.get("category") in deductible_cats)
    taxable = max(0, total_revenue - deductible)
    estimated_tax = calculate_pit(taxable)

    reserve = await db.tax_reserves.find_one({"user_id": user_id}, {"_id": 0})
    tax_reserve = reserve.get("amount", 0) if reserve else 0

    msg = (
        f"*ClearFile Tax Summary*\n\n"
        f"Total Revenue: ₦{total_revenue:,.0f}\n"
        f"Total Expenses: ₦{total_expenses:,.0f}\n"
        f"Net Profit: ₦{total_revenue - total_expenses:,.0f}\n\n"
        f"Estimated VAT Collected: ₦{vat_collected:,.0f}\n"
        f"Estimated Tax Obligation: ₦{estimated_tax:,.0f}\n"
        f"Tax Reserve Set Aside: ₦{tax_reserve:,.0f}\n\n"
        f"*Recommendation:* Keep ₦{vat_collected:,.0f} aside in a separate tax wallet/account for your next filing."
    )

    await send_whatsapp_message(phone, msg)


# ========================
# WEBHOOK ENDPOINTS
# ========================

@router.get("/whatsapp/settings")
async def get_whatsapp_settings(user: dict = Depends(get_current_user)):
    """Get user's WhatsApp notification settings."""
    settings = await db.whatsapp_settings.find_one({"user_id": user["id"]}, {"_id": 0})
    if not settings:
        return {"phone": None, "transaction_notifications": True, "weekly_summary": True, "tax_reminders": True}
    return settings


@router.put("/whatsapp/settings")
async def update_whatsapp_settings(request: Request, user: dict = Depends(get_current_user)):
    """Update WhatsApp notification preferences."""
    data = await request.json()
    allowed = {"transaction_notifications", "weekly_summary", "tax_reminders"}
    update = {k: v for k, v in data.items() if k in allowed}
    if update:
        await db.whatsapp_settings.update_one(
            {"user_id": user["id"]},
            {"$set": update},
            upsert=True
        )
    return {"message": "Settings updated"}


@router.get("/whatsapp/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    """Main WhatsApp webhook — handles all conversation flows."""
    try:
        body = await request.body()
        # Validate Meta signature when app secret is configured
        if WHATSAPP_APP_SECRET:
            import hmac as _hmac
            import hashlib as _hashlib
            sig = request.headers.get("x-hub-signature-256", "")
            expected = "sha256=" + _hmac.new(WHATSAPP_APP_SECRET.encode(), body, _hashlib.sha256).hexdigest()
            if not _hmac.compare_digest(expected, sig):
                logger.warning("WhatsApp webhook: invalid signature rejected")
                raise HTTPException(status_code=403, detail="Invalid signature")
        payload = json.loads(body)
        message_body = ""
        sender = ""
        button_id = None

        if "entry" in payload:
            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    for msg in value.get("messages", []):
                        sender = msg.get("from", "")
                        if msg.get("type") == "text":
                            message_body = msg["text"]["body"]
                        elif msg.get("type") == "interactive":
                            button_id = msg.get("interactive", {}).get("button_reply", {}).get("id", "")
                            message_body = button_id
                        break

        if not message_body and not button_id:
            return {"status": "ok"}

        phone = re.sub(r'[^\d]', '', sender)
        user = await db.users.find_one({"whatsapp_phone": {"$regex": phone[-10:]}})

        if not user:
            await send_whatsapp_message(sender, f"Welcome to ClearFile NG! Link your WhatsApp in the app first.\n{FRONTEND_URL}/settings")
            return {"status": "ok", "message": "User not found"}

        user_id = str(user["_id"])

        # ========== SUBSCRIPTION GATE ==========
        if not is_pro_user(user):
            await send_whatsapp_message(sender, f"This feature requires the Pro plan (₦4,000/month).\n\nUpgrade: {FRONTEND_URL}/settings")
            return {"status": "ok", "message": "Free user"}

        # ========== CHECK CONVERSATION STATE ==========
        conv_state = await get_user_state(user_id)

        if conv_state["state"] == STATE_AWAITING_COMINGLE_REPLY:
            await process_comingle_reply(user_id, sender, message_body, conv_state["data"])
            return {"status": "ok", "flow": "comingle"}

        if conv_state["state"] == STATE_AWAITING_OWNER_CONTRIB:
            await handle_owner_contribution(user_id, sender, conv_state["data"].get("amount", 0), message_body)
            return {"status": "ok", "flow": "owner_contrib"}

        if conv_state["state"] == STATE_AWAITING_INVOICE_MATCH:
            await process_invoice_match_reply(user_id, sender, message_body, conv_state["data"])
            return {"status": "ok", "flow": "invoice_match"}

        if conv_state["state"] == STATE_AWAITING_CATEGORY:
            # Category reply for proactive tagging
            tx_id = conv_state["data"].get("transaction_id")
            category = None
            text_lower = message_body.lower().strip()
            if text_lower.isdigit():
                idx = int(text_lower) - 1
                if 0 <= idx < len(VALID_CATEGORIES[:9]):
                    category = VALID_CATEGORIES[idx]
            if not category:
                for cat in VALID_CATEGORIES:
                    if cat.lower().startswith(text_lower):
                        category = cat
                        break
            if category:
                is_ded = category in DEDUCTIBLE_CATEGORIES
                await db.transactions.update_one(
                    {"id": tx_id, "user_id": user_id},
                    {"$set": {"category": category, "is_business": is_ded, "ai_categorized": True}}
                )
                badge = " [Tax Deductible]" if is_ded else ""
                await send_whatsapp_message(sender, f"Categorized as {category}.{badge}")
                await clear_user_state(user_id)
            else:
                await send_whatsapp_message(sender, "Reply with a number (1-9) or category name.")
            return {"status": "ok", "flow": "category"}

        # ========== COMMANDS ==========
        text_lower = message_body.lower().strip()

        if text_lower in ["hi", "hello", "hey", "help", "menu"]:
            await send_whatsapp_message(sender,
                "*ClearFile NG Bot*\n\n"
                "Log expenses:\n• \"Paid 5k for MTN data\"\n• \"Sent 50k to 0123456789 for rent\"\n\n"
                "Commands:\n"
                "• *summary* — Tax & VAT dashboard\n"
                "• *inject* — Log owner funds\n"
                "• *invoice* — Create invoice\n"
                "• *memory* — View saved categories\n"
                "• *balance* — Quick totals"
            )
            return {"status": "ok"}

        if text_lower in ["summary", "tax", "vat", "dashboard"]:
            await send_tax_summary(user_id, sender)
            return {"status": "ok", "flow": "tax_summary"}

        if text_lower in ["balance", "total"]:
            expenses = await db.transactions.find({"user_id": user_id, "type": "expense", "is_personal": {"$ne": True}}, {"_id": 0, "amount": 1, "category": 1}).limit(1000).to_list(1000)
            total = sum(tx["amount"] for tx in expenses)
            deductible = sum(tx["amount"] for tx in expenses if tx.get("category") in DEDUCTIBLE_CATEGORIES)
            await send_whatsapp_message(sender, f"*Quick Balance*\nBusiness Expenses: ₦{total:,.0f}\nTax Deductible: ₦{deductible:,.0f}\nSavings: ~₦{deductible * 0.2:,.0f}")
            return {"status": "ok"}

        if text_lower in ["memory", "saved"]:
            memories = await db.transaction_memory.find({"user_id": user_id}, {"_id": 0}).sort("updated_at", -1).limit(10).to_list(10)
            if not memories:
                await send_whatsapp_message(sender, "No saved categories yet.")
            else:
                lines = "\n".join(f"• ***{m['receiver_account'][-4:]} → {m['category']}" for m in memories)
                await send_whatsapp_message(sender, f"*Saved Categories:*\n{lines}")
            return {"status": "ok"}

        # ========== OWNER CONTRIBUTION FLOW ==========
        if text_lower.startswith("inject") or "owner money" in text_lower or "fund business" in text_lower:
            amount = parse_amount(message_body)
            if amount and amount > 0:
                await set_user_state(user_id, STATE_AWAITING_OWNER_CONTRIB, {"amount": amount})
                await send_whatsapp_buttons(sender,
                    f"₦{amount:,.0f} — Did you put personal money into the business, or did the business pay you back?",
                    [{"id": "i_funded_business", "title": "I funded business"},
                     {"id": "business_paid_me", "title": "Business paid me"}]
                )
            else:
                await send_whatsapp_message(sender, "How much? Reply: \"inject 200k\" or \"inject N500,000\"")
            return {"status": "ok", "flow": "owner_contrib_start"}

        # ========== INVOICE CREATION ==========
        if text_lower.startswith("invoice"):
            amount = parse_amount(message_body)
            if amount and amount > 0:
                # Extract customer name if present
                parts = message_body.split(" for ")
                customer = parts[1].strip() if len(parts) > 1 else "Customer"
                vat = round(amount * 0.075, 2)
                inv = {
                    "id": str(uuid.uuid4()),
                    "invoice_number": f"INV-{datetime.now().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}",
                    "user_id": user_id,
                    "customer_name": customer,
                    "amount": amount, "vat_amount": vat, "total": round(amount + vat, 2),
                    "status": "unpaid", "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.invoices.insert_one(inv)
                await db.vat_liability.update_one(
                    {"user_id": user_id},
                    {"$inc": {"accrued_vat": vat}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}},
                    upsert=True
                )
                await send_whatsapp_message(sender,
                    f"*Invoice Created*\n{inv['invoice_number']}\nCustomer: {customer}\nAmount: ₦{amount:,.0f}\nVAT (7.5%): ₦{vat:,.0f}\nTotal: ₦{inv['total']:,.0f}\nStatus: Unpaid"
                )
            else:
                await send_whatsapp_message(sender, "Create invoice: \"invoice 500k for Client Name\"")
            return {"status": "ok", "flow": "invoice_create"}

        # ========== STANDARD EXPENSE LOGGING ==========
        parsed_amount = parse_amount(message_body)
        if not parsed_amount or parsed_amount <= 0:
            await send_whatsapp_message(sender, "I couldn't parse that. Try:\n• \"Paid 5k for MTN data\"\n• \"Spent N15,000 on fuel\"\n• \"inject 200k\"")
            return {"status": "ok"}

        category = categorize_text(message_body)
        is_deductible = category in DEDUCTIBLE_CATEGORIES

        # Check receiver account for memory
        account_match = re.search(r'(?:to|account|acct)\s*[:#]?\s*(\d{10})', message_body.lower())
        receiver_account = account_match.group(1) if account_match else None

        if receiver_account:
            remembered = await get_category_from_memory(user_id, receiver_account)
            if remembered:
                category = remembered
                is_deductible = category in DEDUCTIBLE_CATEGORIES

        tx_doc = {
            "id": str(uuid.uuid4()), "user_id": user_id,
            "amount": parsed_amount, "type": "expense", "category": category,
            "description": message_body.strip()[:200],
            "date": datetime.now(timezone.utc).isoformat(),
            "receiver_account": receiver_account,
            "is_recurring": False, "ai_categorized": True, "is_business": is_deductible,
            "flagged": False, "source": "whatsapp",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.transactions.insert_one(tx_doc)
        tx_doc.pop("_id", None)

        if receiver_account and category != "Miscellaneous":
            await save_category_to_memory(user_id, receiver_account, category)

        badge = " [Tax Deductible]" if is_deductible else ""
        memory_msg = f" (Saved for ***{receiver_account[-4:]})" if receiver_account else ""
        ded_msg = " Your estimated tax has been reduced." if is_deductible else ""
        reply = f"Done! ₦{parsed_amount:,.0f} logged under {category}.{badge}{memory_msg}{ded_msg}"

        await send_whatsapp_message(sender, reply)
        return {"status": "ok", "reply": reply, "transaction_id": tx_doc["id"]}

    except Exception as e:
        logger.error(f"WA webhook error: {e}")
        return {"status": "error", "message": str(e)}


# ========================
# MONO WEBHOOK — Co-mingling + Reconciliation
# ========================

@router.post("/whatsapp/mono-sync")
async def process_mono_transaction(request: Request):
    """Called when Mono syncs a new bank transaction. Runs guardrails."""
    data = await request.json()
    user_id = data.get("user_id")
    tx_id = data.get("transaction_id", str(uuid.uuid4()))
    amount = float(data.get("amount", 0))
    description = data.get("description", "")
    tx_type = data.get("type", "debit")
    receiver_account = data.get("receiver_account")

    user = await db.users.find_one({"_id": __import__('bson').ObjectId(user_id)})
    if not user or not is_pro_user(user):
        return {"status": "skipped", "reason": "No user or not pro"}

    phone = user.get("whatsapp_phone", "").replace("+", "")
    if not phone:
        return {"status": "skipped", "reason": "No WhatsApp linked"}

    # === For incoming payments (credits), try invoice reconciliation ===
    if tx_type == "credit" and amount > 0:
        reconciled = await attempt_invoice_reconciliation(user_id, phone, amount, tx_id)
        if reconciled:
            return {"status": "ok", "action": "invoice_reconciled"}

    # === For debits, check co-mingling ===
    if tx_type == "debit":
        # Check memory first
        if receiver_account:
            remembered = await get_category_from_memory(user_id, receiver_account)
            if remembered:
                is_ded = remembered in DEDUCTIBLE_CATEGORIES
                await db.transactions.update_one(
                    {"id": tx_id}, {"$set": {"category": remembered, "is_business": is_ded, "ai_categorized": True}}
                )
                await send_whatsapp_message(phone, f"Auto-labeled: ₦{amount:,.0f} → {remembered}{' [Tax Deductible]' if is_ded else ''}")
                return {"status": "ok", "action": "auto_labeled"}

        # Check for personal spending
        asked = await handle_comingle_check(user_id, phone, {
            "id": tx_id, "amount": amount, "description": description, "merchant": description
        })
        if asked:
            return {"status": "ok", "action": "asked_comingle"}

    return {"status": "ok", "action": "none"}


# ========================
# PROACTIVE TAGGING TRIGGER
# ========================

@router.post("/whatsapp/proactive-tag")
async def trigger_proactive_tag(request: Request):
    """Ask user to categorize an unlabeled transaction."""
    data = await request.json()
    user_id = data.get("user_id")
    tx_id = data.get("transaction_id")
    description = data.get("description", "")
    amount = data.get("amount", 0)
    receiver_account = data.get("receiver_account")

    user = await db.users.find_one({"_id": __import__('bson').ObjectId(user_id)})
    if not user or not is_pro_user(user):
        return {"status": "skipped"}

    phone = user.get("whatsapp_phone", "").replace("+", "")
    if not phone:
        return {"status": "skipped"}

    if receiver_account:
        remembered = await get_category_from_memory(user_id, receiver_account)
        if remembered:
            is_ded = remembered in DEDUCTIBLE_CATEGORIES
            await db.transactions.update_one(
                {"id": tx_id, "user_id": user_id},
                {"$set": {"category": remembered, "is_business": is_ded, "ai_categorized": True}}
            )
            return {"status": "ok", "auto_labeled": True, "category": remembered}

    await set_user_state(user_id, STATE_AWAITING_CATEGORY, {"transaction_id": tx_id})
    cats = "\n".join(f"{i+1}. {c}" for i, c in enumerate(VALID_CATEGORIES[:9]))
    await send_whatsapp_message(phone, f"New transaction: ₦{amount:,.0f} — {description}\n\nWhat category?\n{cats}")
    return {"status": "ok", "asked_user": True}


# ========================
# USER-FACING API ENDPOINTS
# ========================

@router.post("/whatsapp/link")
async def link_whatsapp(request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    phone = data.get("phone", "").strip()
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number required")
    if not is_pro_user(user):
        raise HTTPException(status_code=403, detail="WhatsApp bot requires Pro plan")

    phone = re.sub(r'[^\d+]', '', phone)
    if not phone.startswith("+"):
        phone = "+234" + (phone[1:] if phone.startswith("0") else phone)

    await db.users.update_one({"_id": __import__('bson').ObjectId(user["id"])}, {"$set": {"whatsapp_phone": phone, "whatsapp_linked": True}})
    await send_whatsapp_message(phone.replace("+", ""),
        "*ClearFile NG Connected!*\n\nLog expenses: \"Paid 5k for data\"\nCreate invoices: \"invoice 500k for Client\"\nOwner funds: \"inject 200k\"\nTax summary: \"summary\"\n\nType *help* for all commands.")
    return {"message": "WhatsApp linked", "phone": phone, "bot_number": WHATSAPP_PHONE_NUMBER_ID, "wa_link": f"https://wa.me/{WHATSAPP_PHONE_NUMBER_ID}?text=Hi%20ClearFile%20NG"}


@router.get("/whatsapp/status")
async def get_whatsapp_status(user: dict = Depends(get_current_user)):
    return {"linked": user.get("whatsapp_linked", False), "phone": user.get("whatsapp_phone", ""), "is_pro": is_pro_user(user), "bot_number": WHATSAPP_PHONE_NUMBER_ID}


@router.get("/whatsapp/memory")
async def get_transaction_memory(user: dict = Depends(get_current_user)):
    memories = await db.transaction_memory.find({"user_id": user["id"]}, {"_id": 0}).sort("updated_at", -1).limit(50).to_list(50)
    return {"memories": memories, "count": len(memories)}


@router.delete("/whatsapp/memory/{receiver_account}")
async def delete_memory(receiver_account: str, user: dict = Depends(get_current_user)):
    result = await db.transaction_memory.delete_one({"user_id": user["id"], "receiver_account": receiver_account})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"message": "Deleted"}


@router.post("/whatsapp/test-parse")
async def test_parse_message(request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    text = data.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Text required")
    amount = parse_amount(text)
    category = categorize_text(text)
    return {"input": text, "parsed": {"amount": amount, "category": category, "is_deductible": category in DEDUCTIBLE_CATEGORIES, "is_likely_personal": is_likely_personal(text)}, "would_create": amount is not None and amount > 0}
