"""State vs Federal Tax Clarity Engine + TCC Tracker + Tax Planner"""
import uuid
import io
import os
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER

from database import db
from utils.auth import get_current_user
from utils.tax import calculate_pit, calculate_cit, calculate_vat
from config import NTA_PIT_BANDS

logger = logging.getLogger(__name__)

router = APIRouter()

# Nigerian States and their Revenue Services
NIGERIAN_STATES = {
    "lagos": {"name": "Lagos", "service": "LIRS", "full_name": "Lagos State Internal Revenue Service", "portal": "https://lirs.gov.ng", "paye_account": "LIRS PAYE Collection Account"},
    "rivers": {"name": "Rivers", "service": "RIRS", "full_name": "Rivers State Internal Revenue Service", "portal": "https://rivirs.gov.ng", "paye_account": "RIRS PAYE Collection Account"},
    "abuja": {"name": "FCT Abuja", "service": "FCT-IRS", "full_name": "FCT Internal Revenue Service", "portal": "https://fctirs.gov.ng", "paye_account": "FCT-IRS PAYE Collection Account"},
    "ogun": {"name": "Ogun", "service": "OGIRS", "full_name": "Ogun State Internal Revenue Service", "portal": "https://ogirs.og.gov.ng", "paye_account": "OGIRS PAYE Collection Account"},
    "oyo": {"name": "Oyo", "service": "OYIRS", "full_name": "Oyo State Internal Revenue Service", "portal": "https://oyostatebir.com", "paye_account": "OYIRS PAYE Collection Account"},
    "kano": {"name": "Kano", "service": "KIRS", "full_name": "Kano State Internal Revenue Service", "portal": "https://kirs.gov.ng", "paye_account": "KIRS PAYE Collection Account"},
    "kaduna": {"name": "Kaduna", "service": "KADIRS", "full_name": "Kaduna State Internal Revenue Service", "portal": "https://kadirs.kd.gov.ng", "paye_account": "KADIRS PAYE Collection Account"},
    "enugu": {"name": "Enugu", "service": "ESIRS", "full_name": "Enugu State Internal Revenue Service", "portal": "https://esirs.gov.ng", "paye_account": "ESIRS PAYE Collection Account"},
    "delta": {"name": "Delta", "service": "DBIR", "full_name": "Delta State Board of Internal Revenue", "portal": "https://dbir.gov.ng", "paye_account": "DBIR PAYE Collection Account"},
    "anambra": {"name": "Anambra", "service": "AIRS", "full_name": "Anambra State Internal Revenue Service", "portal": "https://airs.an.gov.ng", "paye_account": "AIRS PAYE Collection Account"},
    "other": {"name": "Other", "service": "State IRS", "full_name": "Your State Internal Revenue Service", "portal": "Contact your state revenue service", "paye_account": "State PAYE Collection Account"},
}


@router.get("/states")
async def get_nigerian_states():
    return {"states": [{"id": k, "name": v["name"], "service": v["service"]} for k, v in NIGERIAN_STATES.items()]}


@router.put("/user/state")
async def update_user_state(request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    state = data.get("state_of_residence", "").lower()
    from bson import ObjectId
    await db.users.update_one(
        {"_id": ObjectId(user["id"])},
        {"$set": {"state_of_residence": state}}
    )
    return {"message": "State updated", "state": state}


@router.get("/tax-obligations")
async def get_tax_obligations(user: dict = Depends(get_current_user)):
    """Route each tax obligation to the correct authority (State vs Federal)."""
    business_type = user.get("business_type", "freelancer")
    state = user.get("state_of_residence", "lagos")
    state_info = NIGERIAN_STATES.get(state, NIGERIAN_STATES["other"])

    user_id = user["id"]
    transactions = await db.transactions.find(
        {"user_id": user_id},
        {"_id": 0, "amount": 1, "type": 1, "category": 1}
    ).sort("date", -1).limit(1000).to_list(1000)

    gross_income = sum(tx["amount"] for tx in transactions if tx["type"] == "income")
    total_expenses = sum(tx["amount"] for tx in transactions if tx["type"] == "expense")
    deductible_cats = {"Rent", "Utilities", "Professional Fees", "Marketing", "Equipment", "Subscriptions"}
    deductible = sum(tx["amount"] for tx in transactions if tx["type"] == "expense" and tx.get("category") in deductible_cats)
    taxable_income = max(0, gross_income - deductible)

    now = datetime.now(timezone.utc)

    # Federal obligations
    federal_obligations = []

    # VAT - always federal for businesses
    if business_type in ["sme", "company"]:
        vat_amount = calculate_vat(gross_income)
        federal_obligations.append({
            "tax_type": "VAT",
            "description": "Value Added Tax (7.5%)",
            "amount": vat_amount,
            "authority": "NRS (Federal)",
            "portal": "https://taxpromax.firs.gov.ng",
            "deadline": "21st of the following month",
            "frequency": "Monthly",
            "next_deadline": (now.replace(day=21) if now.day < 21 else (now.replace(day=21) + __import__('datetime').timedelta(days=32)).replace(day=21)).strftime("%B %d, %Y")
        })

    # CIT - federal for companies
    if business_type == "company":
        cit = calculate_cit(taxable_income, gross_income)
        federal_obligations.append({
            "tax_type": "CIT",
            "description": "Company Income Tax",
            "amount": cit,
            "authority": "NRS (Federal)",
            "portal": "https://taxpromax.firs.gov.ng",
            "deadline": "6 months after financial year end",
            "frequency": "Annual",
            "next_deadline": "June 30, 2026"
        })

    # PIT for freelancers - federal via NRS
    if business_type in ["freelancer", "salary_earner"]:
        pit = calculate_pit(taxable_income)
        federal_obligations.append({
            "tax_type": "PIT",
            "description": "Personal Income Tax (NTA 2025)",
            "amount": pit,
            "authority": "NRS (Federal)",
            "portal": "https://taxpromax.firs.gov.ng",
            "deadline": "March 31st",
            "frequency": "Annual",
            "next_deadline": "March 31, 2027"
        })

    # State obligations
    state_obligations = []

    # PAYE - always state level
    if business_type in ["salary_earner", "company", "sme"]:
        paye_amount = calculate_pit(taxable_income) if business_type == "salary_earner" else taxable_income * 0.1
        state_obligations.append({
            "tax_type": "PAYE",
            "description": "Pay-As-You-Earn",
            "amount": round(paye_amount, 2),
            "authority": f"{state_info['service']} ({state_info['name']} State)",
            "portal": state_info["portal"],
            "deadline": "10th of the following month",
            "frequency": "Monthly",
            "account_info": state_info["paye_account"]
        })

    # Business premises levy - state level
    if business_type in ["sme", "company"]:
        state_obligations.append({
            "tax_type": "Business Premises",
            "description": "Business Premises Levy",
            "amount": 10000,
            "authority": f"{state_info['service']} ({state_info['name']} State)",
            "portal": state_info["portal"],
            "deadline": "March 31st",
            "frequency": "Annual"
        })

    return {
        "federal": federal_obligations,
        "state": state_obligations,
        "state_info": state_info,
        "business_type": business_type,
        "total_federal": round(sum(o["amount"] for o in federal_obligations), 2),
        "total_state": round(sum(o["amount"] for o in state_obligations), 2)
    }


# ========================
# TCC TRACKER
# ========================

@router.get("/tcc/progress")
async def get_tcc_progress(user: dict = Depends(get_current_user)):
    """Track progress towards Tax Clearance Certificate eligibility."""
    user_id = user["id"]

    tx_count = await db.transactions.count_documents({"user_id": user_id})
    receipts_count = await db.receipts.count_documents({"user_id": user_id})
    bank_count = await db.bank_accounts.count_documents({"user_id": user_id})
    has_tin = bool(user.get("tin_number"))

    # Check if taxes assessed and paid (has income + expenses logged)
    income_txs = await db.transactions.count_documents({"user_id": user_id, "type": "income"})
    expense_txs = await db.transactions.count_documents({"user_id": user_id, "type": "expense"})
    taxes_assessed = income_txs >= 3 and expense_txs >= 3

    # Check annual returns (sufficient records)
    annual_returns_filed = tx_count >= 15 and receipts_count >= 2

    checklist = [
        {
            "id": "tin",
            "item": "TIN Linked",
            "completed": has_tin,
            "weight": 25,
            "description": "Add your Tax Identification Number to your profile",
            "fix_route": "/settings",
            "fix_label": "Add TIN"
        },
        {
            "id": "taxes_paid",
            "item": "Current Year Taxes Assessed & Paid",
            "completed": taxes_assessed,
            "weight": 40,
            "description": "Ensure your Net Taxable Profit has a corresponding payment logged",
            "fix_route": "/transactions",
            "fix_label": "Log Payment"
        },
        {
            "id": "returns_filed",
            "item": "Annual Returns Filed",
            "completed": annual_returns_filed,
            "weight": 35,
            "description": "Complete your income statement with all transactions and receipts",
            "fix_route": "/transactions",
            "fix_label": "Complete Records"
        }
    ]

    total_weight = sum(item["weight"] for item in checklist)
    completed_weight = sum(item["weight"] for item in checklist if item["completed"])
    progress = int((completed_weight / total_weight) * 100)

    return {
        "progress": progress,
        "checklist": checklist,
        "completed_count": sum(1 for item in checklist if item["completed"]),
        "total_count": len(checklist),
        "tcc_ready": progress >= 100,
        "next_steps": [item for item in checklist if not item["completed"]]
    }


@router.get("/tcc/generate-letter")
async def generate_tcc_letter(user: dict = Depends(get_current_user)):
    """Generate a TCC Request Letter as PDF."""
    user_name = user.get("name", "User")
    business_type = user.get("business_type", "freelancer")
    state = user.get("state_of_residence", "lagos")
    state_info = NIGERIAN_STATES.get(state, NIGERIAN_STATES["other"])

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='LetterTitle', fontSize=16, alignment=TA_CENTER, textColor=colors.HexColor('#006400'), spaceAfter=20, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='LetterBody', fontSize=11, spaceAfter=12, leading=16))
    styles.add(ParagraphStyle(name='LetterRef', fontSize=10, spaceAfter=6, textColor=colors.grey))

    elements = []

    # Header
    elements.append(Paragraph("ClearFile NG", styles['LetterTitle']))
    elements.append(Paragraph("TAX CLEARANCE CERTIFICATE REQUEST LETTER", styles['Heading2']))
    elements.append(Spacer(1, 20))

    # Date and reference
    elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", styles['LetterRef']))
    elements.append(Paragraph(f"Ref: CFNG/TCC/{datetime.now().strftime('%Y%m%d')}/{user['id'][:8]}", styles['LetterRef']))
    elements.append(Spacer(1, 20))

    # Addressee
    elements.append(Paragraph("The Director,", styles['LetterBody']))
    elements.append(Paragraph(f"{state_info['full_name']},", styles['LetterBody']))
    elements.append(Paragraph(f"{state_info['name']} State.", styles['LetterBody']))
    elements.append(Spacer(1, 15))

    # Subject
    elements.append(Paragraph("<b>RE: APPLICATION FOR TAX CLEARANCE CERTIFICATE</b>", styles['LetterBody']))
    elements.append(Spacer(1, 10))

    # Body
    body_text = f"""
    Dear Sir/Madam,<br/><br/>
    I, <b>{user_name}</b>, writing as a <b>{business_type.replace('_', ' ').title()}</b>, hereby apply for a Tax Clearance Certificate (TCC) 
    for the assessment year ending December 31, {datetime.now().year - 1}.<br/><br/>
    I confirm that I have:<br/>
    - Filed all required tax returns for the relevant assessment years<br/>
    - Paid all outstanding tax liabilities<br/>
    - Maintained proper books of accounts and financial records<br/>
    - No outstanding penalties or fines with any tax authority<br/><br/>
    I have attached the following supporting documents:<br/>
    1. Evidence of tax payments<br/>
    2. Filed tax returns<br/>
    3. Bank statements showing income and expenses<br/>
    4. Financial records and receipts<br/><br/>
    I kindly request the issuance of my Tax Clearance Certificate at your earliest convenience.<br/><br/>
    Thank you for your cooperation.
    """
    elements.append(Paragraph(body_text, styles['LetterBody']))
    elements.append(Spacer(1, 30))

    # Signature
    elements.append(Paragraph(f"Yours faithfully,", styles['LetterBody']))
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(f"<b>{user_name}</b>", styles['LetterBody']))
    elements.append(Spacer(1, 40))

    # Footer
    elements.append(Paragraph("Generated by ClearFile NG - Nigerian Tax & Expense Management",
                              ParagraphStyle(name='Footer', fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=tcc_request_letter_{datetime.now().year}.pdf"}
    )


# ========================
# TAX PLANNER (What-If Simulator)
# ========================

@router.post("/tax-planner/simulate")
async def simulate_tax(request: Request, user: dict = Depends(get_current_user)):
    """What-If tax scenario simulator."""
    data = await request.json()

    annual_income = float(data.get("annual_income", 0))
    annual_expenses = float(data.get("annual_expenses", 0))
    business_type = data.get("business_type") or user.get("business_type", "freelancer")

    deductible_pct = float(data.get("deductible_percentage", 70)) / 100
    deductible_expenses = annual_expenses * deductible_pct
    taxable_income = max(0, annual_income - deductible_expenses)

    # Calculate taxes
    if business_type == "company":
        income_tax = calculate_cit(taxable_income, annual_income)
        tax_type = "Company Income Tax (NTA 2025)"
    else:
        income_tax = calculate_pit(taxable_income)
        tax_type = "Personal Income Tax (NTA 2025)"

    vat = calculate_vat(annual_income) if business_type in ["sme", "company"] else 0
    total_tax = income_tax + vat

    after_tax = annual_income - total_tax - annual_expenses
    monthly_savings_needed = round(total_tax / 12, 2)
    effective_rate = round((total_tax / max(annual_income, 1)) * 100, 1)

    return {
        "annual_income": annual_income,
        "annual_expenses": annual_expenses,
        "deductible_expenses": round(deductible_expenses, 2),
        "taxable_income": round(taxable_income, 2),
        "income_tax": income_tax,
        "vat": vat,
        "total_tax": total_tax,
        "tax_type": tax_type,
        "after_tax_income": round(after_tax, 2),
        "monthly_tax_savings": monthly_savings_needed,
        "effective_tax_rate": effective_rate,
        "breakdown": {
            "income": annual_income,
            "tax": total_tax,
            "expenses": annual_expenses,
            "take_home": max(0, after_tax)
        }
    }


@router.post("/tax-planner/set-aside")
async def set_aside_tax_reserve(request: Request, user: dict = Depends(get_current_user)):
    """Mark a portion of balance as tax reserve."""
    data = await request.json()
    amount = float(data.get("amount", 0))

    from bson import ObjectId
    reserve = await db.tax_reserves.find_one({"user_id": user["id"]})
    current = reserve.get("amount", 0) if reserve else 0

    await db.tax_reserves.update_one(
        {"user_id": user["id"]},
        {"$set": {"amount": current + amount, "updated_at": datetime.now(timezone.utc).isoformat()},
         "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )

    return {"message": f"Set aside N{amount:,.0f} for tax reserve", "total_reserve": round(current + amount, 2)}


@router.get("/tax-planner/reserve")
async def get_tax_reserve(user: dict = Depends(get_current_user)):
    reserve = await db.tax_reserves.find_one({"user_id": user["id"]}, {"_id": 0})
    return {"amount": reserve.get("amount", 0) if reserve else 0}


# ========================
# AI SMART EXPENSE CATEGORIZER
# ========================

@router.post("/categorize/auto")
async def auto_categorize_transactions(user: dict = Depends(get_current_user)):
    """AI-powered categorization: separate personal vs business, flag tax-deductible."""
    user_id = user["id"]
    business_type = user.get("business_type", "freelancer")

    # Tax-deductible expense categories
    DEDUCTIBLE_CATEGORIES = {
        "Rent": "Office/business premises rent",
        "Utilities": "Internet, electricity, water for business",
        "Professional Fees": "Legal, accounting, consulting fees",
        "Marketing": "Advertising and promotion costs",
        "Equipment": "Business equipment and tools",
        "Subscriptions": "Business software and services",
        "Transport": "Business travel and logistics",
    }

    PERSONAL_CATEGORIES = {"Food", "Entertainment", "Shopping", "Personal", "Miscellaneous"}

    transactions = await db.transactions.find(
        {"user_id": user_id, "type": "expense"},
        {"_id": 0, "id": 1, "amount": 1, "category": 1, "description": 1, "is_business": 1}
    ).sort("date", -1).limit(500).to_list(500)

    categorized = []
    total_deductible = 0
    total_personal = 0

    for tx in transactions:
        cat = tx.get("category", "Miscellaneous")
        is_deductible = cat in DEDUCTIBLE_CATEGORIES
        is_business = tx.get("is_business", is_deductible)

        if is_deductible:
            total_deductible += tx["amount"]
        else:
            total_personal += tx["amount"]

        categorized.append({
            "id": tx["id"],
            "amount": tx["amount"],
            "category": cat,
            "description": tx.get("description", ""),
            "is_deductible": is_deductible,
            "is_business": is_business,
            "deduction_reason": DEDUCTIBLE_CATEGORIES.get(cat, None)
        })

    # Calculate tax savings from deductions
    if business_type == "company":
        tax_without = calculate_cit(total_deductible + total_personal, (total_deductible + total_personal) * 3)
        tax_with = calculate_cit(total_personal, total_personal * 3)
    else:
        tax_without = calculate_pit(total_deductible + total_personal)
        tax_with = calculate_pit(total_personal)

    tax_savings = round(tax_without - tax_with, 2)

    return {
        "transactions": categorized[:100],
        "summary": {
            "total_deductible": round(total_deductible, 2),
            "total_personal": round(total_personal, 2),
            "deductible_count": sum(1 for t in categorized if t["is_deductible"]),
            "personal_count": sum(1 for t in categorized if not t["is_deductible"]),
            "estimated_tax_savings": tax_savings,
        },
        "deductible_categories": DEDUCTIBLE_CATEGORIES
    }
