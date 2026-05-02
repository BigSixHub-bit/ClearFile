from datetime import datetime, timezone
from fastapi import APIRouter, Depends

from database import db
from utils.auth import get_current_user

router = APIRouter()

TAX_ARTICLES = [
    {
        "id": "1",
        "title": "Understanding PITA: Personal Income Tax in Nigeria",
        "summary": "Learn how personal income tax works for freelancers and self-employed individuals",
        "content": """
Personal Income Tax Act (PITA) applies to individuals, sole proprietorships, and partnerships in Nigeria.

**Tax Rates (Progressive):**
- First N300,000: 7%
- Next N300,000: 11%
- Next N500,000: 15%
- Next N500,000: 19%
- Next N1,600,000: 21%
- Above N3,200,000: 24%

**Who Pays PITA?**
- Freelancers and consultants
- Self-employed professionals
- Sole proprietors
- Partners in partnerships

**Filing Deadline:** March 31st of the following year
        """,
        "category": "basics"
    },
    {
        "id": "2",
        "title": "VAT in Nigeria: Everything You Need to Know",
        "summary": "A complete guide to Value Added Tax at 7.5% for Nigerian businesses",
        "content": """
Value Added Tax (VAT) is charged at 7.5% on most goods and services in Nigeria.

**VAT Registration:**
- Mandatory for businesses with turnover above threshold
- Must register within 6 months of commencing business

**Filing:**
- Monthly filing required
- Due by 21st of the following month
- File via TaxPro-Max portal

**VAT Exempt Items:**
- Basic food items
- Medical and pharmaceutical products
- Educational materials
- Baby products
        """,
        "category": "vat"
    },
    {
        "id": "3",
        "title": "Tax Deductible Expenses: Maximize Your Savings",
        "summary": "Learn which business expenses can reduce your tax bill",
        "content": """
Properly recording deductible expenses can significantly reduce your tax liability.

**Common Deductible Expenses:**
- Office rent and utilities
- Employee salaries and benefits
- Professional services (legal, accounting)
- Marketing and advertising
- Business travel and transport
- Equipment and supplies
- Insurance premiums
- Bank charges and interest

**Documentation Required:**
- Keep all receipts and invoices
- Maintain proper records for 6 years
- Ensure expenses are wholly and exclusively for business
        """,
        "category": "deductions"
    },
    {
        "id": "4",
        "title": "Finance Act 2023/2024: Key Changes",
        "summary": "Important updates from recent Nigerian tax legislation",
        "content": """
The Finance Acts of 2023 and 2024 introduced several changes:

**Key Changes:**
- VAT rate remains at 7.5%
- New exemptions for small businesses
- Digital services taxation framework
- Updated transfer pricing rules
- Revised penalties for late filing

**Impact on Businesses:**
- More emphasis on electronic filing
- Stricter compliance requirements
- New incentives for SMEs
        """,
        "category": "updates"
    }
]


@router.get("/tax-filing/guide")
async def get_filing_guide(user: dict = Depends(get_current_user)):
    business_type = user.get("business_type", "freelancer")

    common_steps = [
        {"step": 1, "title": "Register on TaxPro-Max", "description": "Visit taxpromax.firs.gov.ng and create an account with your TIN"},
        {"step": 2, "title": "Gather Documents", "description": "Prepare income statements, expense receipts, and bank statements"},
        {"step": 3, "title": "Calculate Taxable Income", "description": "Use ClearFile NG's tax calculator for accurate estimates"},
        {"step": 4, "title": "Complete Tax Return", "description": "Fill in the appropriate forms on TaxPro-Max portal"},
        {"step": 5, "title": "Submit and Pay", "description": "Submit your return and pay any tax owed via bank transfer or card"}
    ]

    documents_needed = [
        "Tax Identification Number (TIN)",
        "Bank statements for the tax year",
        "Income receipts and invoices",
        "Expense receipts (properly categorized)",
        "Previous year's tax returns (if any)",
        "Business registration documents"
    ]

    if business_type == "company":
        documents_needed.extend([
            "Certificate of Incorporation",
            "Audited Financial Statements",
            "Board Resolution for tax filing"
        ])

    deadlines = {
        "vat": "21st of the following month",
        "paye": "10th of the following month",
        "annual_cit": "6 months after financial year end",
        "annual_pit": "March 31st"
    }

    return {
        "steps": common_steps,
        "documents_needed": documents_needed,
        "deadlines": deadlines,
        "firs_portal": "https://taxpromax.firs.gov.ng",
        "business_type": business_type
    }


@router.get("/tax-filing/checklist")
async def get_filing_checklist(user: dict = Depends(get_current_user)):
    user_id = user["id"]
    transactions = await db.transactions.count_documents({"user_id": user_id})
    receipts = await db.receipts.count_documents({"user_id": user_id})
    bank_accounts = await db.bank_accounts.count_documents({"user_id": user_id})

    checklist = [
        {"item": "Create ClearFile NG account", "completed": True},
        {"item": "Set business type", "completed": user.get("business_type") is not None},
        {"item": "Link bank account", "completed": bank_accounts > 0},
        {"item": "Track at least 10 transactions", "completed": transactions >= 10},
        {"item": "Upload expense receipts", "completed": receipts > 0},
        {"item": "Review flagged transactions", "completed": False},
        {"item": "Generate tax report", "completed": False},
        {"item": "Register on FIRS TaxPro-Max", "completed": False}
    ]

    completed_count = sum(1 for item in checklist if item["completed"])
    return {
        "checklist": checklist,
        "completed_count": completed_count,
        "total_count": len(checklist),
        "progress_percentage": int((completed_count / len(checklist)) * 100)
    }


@router.get("/education/articles")
async def get_education_articles(category: str = None):
    if category:
        return [a for a in TAX_ARTICLES if a["category"] == category]
    return TAX_ARTICLES


@router.get("/education/articles/{article_id}")
async def get_article(article_id: str):
    for article in TAX_ARTICLES:
        if article["id"] == article_id:
            return article
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Article not found")
