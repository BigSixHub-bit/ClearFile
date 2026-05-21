"""AI Tax Guide + Expert Matching endpoints"""
import uuid
import os
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request

from database import db
from utils.auth import get_current_user
from utils.tax import calculate_pita, calculate_cita, calculate_vat
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/tax-guide/ai-walkthrough")
async def ai_tax_walkthrough(request: Request, user: dict = Depends(get_current_user)):
    """Generate personalized AI step-by-step FIRS filing guide using user's data."""
    data = await request.json()
    step = data.get("step", 1)
    session_id = data.get("session_id") or f"taxguide-{user['id']}-{uuid.uuid4().hex[:8]}"

    user_id = user["id"]
    business_type = user.get("business_type", "freelancer")
    state = user.get("state_of_residence", "lagos")

    # Fetch user's actual tax data
    transactions = await db.transactions.find(
        {"user_id": user_id},
        {"_id": 0, "amount": 1, "type": 1, "category": 1}
    ).limit(1000).to_list(1000)

    gross_income = sum(tx["amount"] for tx in transactions if tx["type"] == "income")
    total_expenses = sum(tx["amount"] for tx in transactions if tx["type"] == "expense")
    deductible_cats = {"Rent", "Utilities", "Professional Fees", "Marketing", "Equipment", "Subscriptions", "Transport"}
    deductible = sum(tx["amount"] for tx in transactions if tx["type"] == "expense" and tx.get("category") in deductible_cats)
    taxable_income = max(0, gross_income - deductible)

    if business_type == "company":
        income_tax = calculate_cita(taxable_income, gross_income)
        tax_type = "CITA"
    else:
        income_tax = calculate_pita(taxable_income)
        tax_type = "PITA"

    vat = calculate_vat(gross_income) if business_type in ["sme", "company"] else 0
    total_tax = income_tax + vat

    # The 6 filing steps
    steps_guide = {
        1: {
            "title": "Register / Log in to TaxPro-Max",
            "portal": "https://taxpromax.firs.gov.ng",
            "instructions": [
                "Visit the FIRS TaxPro-Max portal at taxpromax.firs.gov.ng",
                "If first time: Click 'Sign Up' and register with your TIN (Tax Identification Number)",
                "If returning: Log in with your email and password",
                "Ensure your profile details match your business registration"
            ],
            "tip": "If you don't have a TIN, visit any FIRS office or apply online at jtb.gov.ng"
        },
        2: {
            "title": "Select the Correct Return Form",
            "portal": "https://taxpromax.firs.gov.ng",
            "instructions": [
                f"After login, navigate to 'File Returns' in the menu",
                f"Select return type: {'Company Income Tax (CITA)' if business_type == 'company' else 'Personal Income Tax (PITA)'}",
                f"Choose the assessment year: {datetime.now().year - 1}",
                "Click 'Start Filing' to begin the form"
            ],
            "tip": f"Your business type ({business_type}) determines which form to use"
        },
        3: {
            "title": "Enter Your Income Details",
            "portal": None,
            "instructions": [
                f"Total Gross Income: Enter N{gross_income:,.0f}",
                "Break down by source if required (sales, services, consulting, etc.)",
                f"Your income categories from ClearFile NG:",
            ],
            "your_data": {
                "gross_income": gross_income,
                "income_breakdown": {}
            },
            "tip": "Use your ClearFile NG records as the source of truth"
        },
        4: {
            "title": "Claim Your Deductible Expenses",
            "portal": None,
            "instructions": [
                f"Total Deductible Expenses: Enter N{deductible:,.0f}",
                "Deductible categories: Rent, Utilities, Professional Fees, Marketing, Equipment, Subscriptions, Transport",
                f"Non-deductible expenses (excluded): N{total_expenses - deductible:,.0f}",
                "Upload supporting receipts if requested"
            ],
            "your_data": {
                "deductible_expenses": deductible,
                "taxable_income": taxable_income
            },
            "tip": f"This reduces your taxable income from N{gross_income:,.0f} to N{taxable_income:,.0f}"
        },
        5: {
            "title": "Review Your Tax Calculation",
            "portal": None,
            "instructions": [
                f"Taxable Income: N{taxable_income:,.0f}",
                f"{tax_type} Tax: N{income_tax:,.0f}",
                f"{'VAT (7.5%): N' + f'{vat:,.0f}' if vat > 0 else 'VAT: Not applicable for your category'}",
                f"Total Tax Owed: N{total_tax:,.0f}",
                "Verify the portal's calculation matches these figures",
                "If there's a discrepancy, check your income and expense entries"
            ],
            "your_data": {
                "income_tax": income_tax,
                "vat": vat,
                "total_tax": total_tax,
                "tax_type": tax_type
            },
            "tip": "The portal will auto-calculate based on your entries. Compare with ClearFile NG estimates."
        },
        6: {
            "title": "Submit & Make Payment",
            "portal": "https://taxpromax.firs.gov.ng",
            "instructions": [
                "Review all entries one final time",
                "Click 'Submit Return' to file",
                f"Total amount to pay: N{total_tax:,.0f}",
                "Payment options: Bank transfer, Card payment, or ePayment",
                "Download and save your filing receipt as proof",
                "You'll receive an acknowledgement email from FIRS"
            ],
            "your_data": {
                "total_to_pay": total_tax
            },
            "tip": f"Keep your filing receipt — you'll need it for your Tax Clearance Certificate (TCC)"
        }
    }

    current_step = steps_guide.get(step, steps_guide[1])

    # Get AI-powered personalized advice for this step
    ai_advice = None
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if api_key:
        try:
            chat = LlmChat(
                api_key=api_key,
                session_id=session_id,
                system_message=(
                    "You are a Nigerian tax filing expert. Give a brief, practical tip (2-3 sentences max) "
                    f"for a {business_type} in {state} state who is on Step {step} of filing on FIRS TaxPro-Max. "
                    "Be specific to their data. No greetings."
                )
            ).with_model("anthropic", "claude-sonnet-4-5-20250929")

            prompt = f"Step {step}: {current_step['title']}. Their gross income is N{gross_income:,.0f}, deductible expenses N{deductible:,.0f}, total tax N{total_tax:,.0f}."
            ai_advice = await chat.send_message(UserMessage(text=prompt))
        except Exception as e:
            logger.warning(f"AI guide advice failed: {e}")

    return {
        "step": step,
        "total_steps": 6,
        "session_id": session_id,
        "title": current_step["title"],
        "portal": current_step.get("portal"),
        "instructions": current_step["instructions"],
        "tip": current_step.get("tip"),
        "your_data": current_step.get("your_data"),
        "ai_advice": ai_advice,
        "user_summary": {
            "business_type": business_type,
            "state": state,
            "gross_income": gross_income,
            "total_tax": total_tax,
            "tax_type": tax_type
        }
    }


# ========================
# EXPERT MATCHING
# ========================

@router.post("/experts/request")
async def request_expert(request: Request, user: dict = Depends(get_current_user)):
    """Submit a request for a verified tax expert."""
    data = await request.json()

    request_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "user_email": user.get("email"),
        "user_name": user.get("name"),
        "business_type": user.get("business_type", "freelancer"),
        "state": user.get("state_of_residence", "lagos"),
        "contact_phone": data.get("phone", ""),
        "contact_email": data.get("email", user.get("email")),
        "service_type": data.get("service_type", "full_filing"),
        "tax_year": data.get("tax_year", str(datetime.now().year - 1)),
        "urgency": data.get("urgency", "normal"),
        "budget_range": data.get("budget_range", ""),
        "notes": data.get("notes", ""),
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await db.expert_requests.insert_one(request_doc)
    request_doc.pop("_id", None)

    # Create notification
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "title": "Expert Request Submitted",
        "message": f"Your request for a tax expert has been submitted. We'll match you within 24-48 hours.",
        "type": "info",
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    return {
        "message": "Expert request submitted successfully",
        "request_id": request_doc["id"],
        "estimated_match_time": "24-48 hours"
    }


@router.get("/experts/requests")
async def get_expert_requests(user: dict = Depends(get_current_user)):
    """Get user's expert match requests."""
    requests = await db.expert_requests.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    return {"requests": requests}
