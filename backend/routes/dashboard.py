from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends

from database import db
from utils.auth import get_current_user
from utils.tax import calculate_pita, calculate_cita, calculate_vat
from config import PITA_RATES

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(user: dict = Depends(get_current_user)):
    user_id = user["id"]
    now = datetime.now(timezone.utc)

    all_user_transactions = await db.transactions.find({"user_id": user_id}, {"_id": 0}).to_list(10000)
    transactions = all_user_transactions

    total_income = sum(tx["amount"] for tx in transactions if tx["type"] == "income")
    total_expenses = sum(tx["amount"] for tx in transactions if tx["type"] == "expense")
    net_income = total_income - total_expenses

    bank_accounts = await db.bank_accounts.find({"user_id": user_id}, {"_id": 0}).to_list(10)
    total_bank_balance = sum(acc.get("balance", 0) for acc in bank_accounts)

    business_type = user.get("business_type", "freelancer")
    deductible_expenses = total_expenses * 0.7
    taxable_income = max(0, total_income - deductible_expenses)

    if business_type == "company":
        estimated_tax = calculate_cita(taxable_income, total_income * 12)
    else:
        estimated_tax = calculate_pita(taxable_income)

    vat_owed = calculate_vat(total_income) if business_type in ["sme", "company"] else 0

    categorized_count = sum(1 for tx in all_user_transactions if tx.get("category"))
    total_tx_count = len(all_user_transactions) or 1
    receipts = await db.receipts.count_documents({"user_id": user_id})
    categorization_score = (categorized_count / total_tx_count) * 40
    receipt_score = min(receipts * 5, 30)
    tracking_score = 30 if len(bank_accounts) > 0 else 15
    tax_health_score = min(100, int(categorization_score + receipt_score + tracking_score))

    spending_breakdown = {}
    for tx in transactions:
        if tx["type"] == "expense":
            cat = tx.get("category", "Miscellaneous")
            spending_breakdown[cat] = spending_breakdown.get(cat, 0) + tx["amount"]

    flagged_count = await db.transactions.count_documents({"user_id": user_id, "flagged": True})

    next_vat_deadline = (now.replace(day=21) + timedelta(days=32)).replace(day=21)

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_income": net_income,
        "total_bank_balance": total_bank_balance,
        "estimated_tax": estimated_tax,
        "vat_owed": vat_owed,
        "tax_health_score": tax_health_score,
        "spending_breakdown": spending_breakdown,
        "flagged_transactions_count": flagged_count,
        "bank_accounts_count": len(bank_accounts),
        "upcoming_deadlines": [
            {"name": "VAT Filing", "date": next_vat_deadline.strftime("%B %d, %Y")},
            {"name": "Annual Returns", "date": "March 31, 2026"}
        ],
        "business_type": business_type,
        "subscription_plan": user.get("subscription_plan", "starter")
    }


@router.get("/tax-calculation")
async def calculate_taxes(user: dict = Depends(get_current_user)):
    user_id = user["id"]
    business_type = user.get("business_type", "freelancer")

    year_start = datetime.now(timezone.utc).replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    transactions = await db.transactions.find({
        "user_id": user_id,
        "date": {"$gte": year_start.isoformat()}
    }, {"_id": 0}).to_list(10000)

    gross_income = sum(tx["amount"] for tx in transactions if tx["type"] == "income")
    total_expenses = sum(tx["amount"] for tx in transactions if tx["type"] == "expense")

    deductible_categories = ["Rent", "Utilities", "Professional Fees", "Marketing", "Equipment", "Subscriptions"]
    deductible_expenses = sum(
        tx["amount"] for tx in transactions
        if tx["type"] == "expense" and tx.get("category") in deductible_categories
    )
    taxable_income = max(0, gross_income - deductible_expenses)

    if business_type == "company":
        income_tax = calculate_cita(taxable_income, gross_income)
        tax_type = "Company Income Tax (CITA)"
    else:
        income_tax = calculate_pita(taxable_income)
        tax_type = "Personal Income Tax (PITA)"

    vat = calculate_vat(gross_income) if business_type in ["sme", "company"] else 0
    non_deducted = total_expenses - deductible_expenses
    potential_savings = non_deducted * 0.2

    return {
        "gross_income": gross_income,
        "total_expenses": total_expenses,
        "deductible_expenses": deductible_expenses,
        "taxable_income": taxable_income,
        "income_tax": income_tax,
        "tax_type": tax_type,
        "vat": vat,
        "total_tax_owed": income_tax + vat,
        "potential_savings": potential_savings,
        "business_type": business_type,
        "tax_brackets": PITA_RATES if business_type != "company" else None,
        "disclaimer": "This estimate is for guidance. Consult a certified tax professional for your final filing."
    }
