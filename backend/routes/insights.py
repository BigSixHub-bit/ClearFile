import os
import logging
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from fastapi import APIRouter, HTTPException, Depends

from database import db
from utils.auth import get_current_user
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/insights/recurring")
async def detect_recurring_expenses(user: dict = Depends(get_current_user)):
    """Detect recurring transactions based on amount/description patterns."""
    user_id = user["id"]

    transactions = await db.transactions.find(
        {"user_id": user_id, "type": "expense"},
        {"_id": 0}
    ).sort("date", -1).to_list(5000)

    if not transactions:
        return {"recurring": [], "total_monthly_recurring": 0}

    # Group by description similarity and amount
    amount_groups = defaultdict(list)
    for tx in transactions:
        key = f"{tx.get('category', 'Other')}|{round(tx['amount'], -2)}"
        amount_groups[key].append(tx)

    recurring = []
    for key, txs in amount_groups.items():
        if len(txs) < 2:
            continue

        # Check if transactions are roughly periodic
        dates = []
        for tx in txs:
            try:
                d = datetime.fromisoformat(tx["date"].replace("Z", "+00:00"))
                dates.append(d)
            except (ValueError, TypeError):
                continue

        if len(dates) < 2:
            continue

        dates.sort()
        intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]

        if not intervals:
            continue

        avg_interval = sum(intervals) / len(intervals)

        # Determine frequency
        if 25 <= avg_interval <= 35:
            frequency = "Monthly"
        elif 12 <= avg_interval <= 17:
            frequency = "Bi-weekly"
        elif 5 <= avg_interval <= 9:
            frequency = "Weekly"
        elif 80 <= avg_interval <= 100:
            frequency = "Quarterly"
        elif 350 <= avg_interval <= 380:
            frequency = "Yearly"
        else:
            continue

        avg_amount = sum(tx["amount"] for tx in txs) / len(txs)
        category = txs[0].get("category", "Other")
        descriptions = list(set(tx.get("description", "") for tx in txs[:3]))

        recurring.append({
            "category": category,
            "amount": round(avg_amount, 2),
            "frequency": frequency,
            "occurrences": len(txs),
            "last_date": txs[0].get("date", ""),
            "descriptions": descriptions[:2],
            "estimated_monthly": round(avg_amount * (30 / max(avg_interval, 1)), 2)
        })

    # Sort by estimated monthly cost
    recurring.sort(key=lambda x: x["estimated_monthly"], reverse=True)

    total_monthly = sum(r["estimated_monthly"] for r in recurring)

    return {
        "recurring": recurring[:15],
        "total_monthly_recurring": round(total_monthly, 2),
        "total_detected": len(recurring)
    }


@router.get("/insights/spending")
async def get_spending_insights(user: dict = Depends(get_current_user)):
    """AI-powered spending analysis and recommendations."""
    user_id = user["id"]
    business_type = user.get("business_type", "freelancer")

    # Get recent transactions
    three_months_ago = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    transactions = await db.transactions.find(
        {"user_id": user_id},
        {"_id": 0, "user_id": 0}
    ).sort("date", -1).to_list(500)

    if not transactions:
        return {
            "insights": [
                {
                    "type": "info",
                    "title": "Start Tracking",
                    "message": "Add your first transactions to get personalized spending insights.",
                    "action": "Add Transaction"
                }
            ],
            "summary": {}
        }

    # Compute spending stats
    total_income = sum(tx["amount"] for tx in transactions if tx["type"] == "income")
    total_expenses = sum(tx["amount"] for tx in transactions if tx["type"] == "expense")

    expense_by_cat = defaultdict(float)
    income_by_cat = defaultdict(float)
    for tx in transactions:
        if tx["type"] == "expense":
            expense_by_cat[tx.get("category", "Other")] += tx["amount"]
        else:
            income_by_cat[tx.get("category", "Other")] += tx["amount"]

    # Generate rule-based insights (always available, no AI needed)
    insights = []

    # Savings rate insight
    if total_income > 0:
        savings_rate = ((total_income - total_expenses) / total_income) * 100
        if savings_rate < 10:
            insights.append({
                "type": "warning",
                "title": "Low Savings Rate",
                "message": f"Your savings rate is {savings_rate:.0f}%. Nigerian financial experts recommend saving at least 20% of income.",
                "action": "Review Expenses"
            })
        elif savings_rate >= 30:
            insights.append({
                "type": "success",
                "title": "Great Savings Rate",
                "message": f"Your savings rate is {savings_rate:.0f}%. You're doing well! Consider investing the surplus.",
                "action": None
            })

    # Top expense category
    if expense_by_cat:
        top_cat = max(expense_by_cat, key=expense_by_cat.get)
        top_pct = (expense_by_cat[top_cat] / total_expenses * 100) if total_expenses > 0 else 0
        if top_pct > 40:
            insights.append({
                "type": "warning",
                "title": f"High {top_cat} Spending",
                "message": f"{top_cat} makes up {top_pct:.0f}% of your expenses (N{expense_by_cat[top_cat]:,.0f}). Consider if this can be optimized.",
                "action": "View Breakdown"
            })

    # Tax deduction opportunity
    deductible_cats = {"Rent", "Utilities", "Professional Fees", "Marketing", "Equipment", "Subscriptions"}
    deductible_total = sum(expense_by_cat.get(c, 0) for c in deductible_cats)
    non_deductible = total_expenses - deductible_total
    if non_deductible > total_expenses * 0.3 and total_expenses > 0:
        insights.append({
            "type": "info",
            "title": "Tax Deduction Opportunity",
            "message": f"N{non_deductible:,.0f} of your expenses aren't categorized as deductible. Properly categorizing could save you up to N{non_deductible * 0.2:,.0f} in taxes.",
            "action": "Categorize Expenses"
        })

    # Month-over-month trend
    now = datetime.now(timezone.utc)
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)

    this_month_expenses = sum(
        tx["amount"] for tx in transactions
        if tx["type"] == "expense" and tx.get("date", "") >= this_month_start.isoformat()
    )
    last_month_expenses = sum(
        tx["amount"] for tx in transactions
        if tx["type"] == "expense"
        and tx.get("date", "") >= last_month_start.isoformat()
        and tx.get("date", "") < this_month_start.isoformat()
    )

    if last_month_expenses > 0:
        change_pct = ((this_month_expenses - last_month_expenses) / last_month_expenses) * 100
        if change_pct > 20:
            insights.append({
                "type": "warning",
                "title": "Spending Increase",
                "message": f"Your expenses are up {change_pct:.0f}% compared to last month (N{this_month_expenses:,.0f} vs N{last_month_expenses:,.0f}).",
                "action": "View Transactions"
            })
        elif change_pct < -15:
            insights.append({
                "type": "success",
                "title": "Spending Decreased",
                "message": f"Great job! You spent {abs(change_pct):.0f}% less than last month.",
                "action": None
            })

    # VAT reminder for businesses
    if business_type in ["sme", "company"] and total_income > 0:
        vat_estimate = total_income * 0.075
        insights.append({
            "type": "info",
            "title": "VAT Estimate",
            "message": f"Based on your income, your estimated VAT liability is N{vat_estimate:,.0f}. Remember to file by the 21st.",
            "action": "View Tax Calculator"
        })

    # Try AI-powered insight
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if api_key and len(transactions) >= 5:
        try:
            # Prepare a summary for AI
            spending_summary = f"""
Business type: {business_type}
Total income: N{total_income:,.0f}
Total expenses: N{total_expenses:,.0f}
Top expense categories: {', '.join(f'{k}: N{v:,.0f}' for k, v in sorted(expense_by_cat.items(), key=lambda x: -x[1])[:5])}
Transaction count: {len(transactions)}
"""
            chat = LlmChat(
                api_key=api_key,
                session_id=f"nairatrack-insights-{user_id}",
                system_message="You are a Nigerian financial advisor. Give ONE specific, actionable tip (2 sentences max) based on the spending data. Focus on Nigerian tax optimization. No greetings."
            ).with_model("anthropic", "claude-sonnet-4-5-20250929")

            response = await chat.send_message(UserMessage(text=spending_summary))

            if response and len(response.strip()) > 10:
                insights.append({
                    "type": "ai",
                    "title": "AI Insight",
                    "message": response.strip()[:300],
                    "action": "Chat with Assistant"
                })
        except Exception as e:
            logger.warning(f"AI insight generation failed: {e}")

    return {
        "insights": insights[:8],
        "summary": {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "savings_rate": round(((total_income - total_expenses) / max(total_income, 1)) * 100, 1),
            "top_expense_category": max(expense_by_cat, key=expense_by_cat.get) if expense_by_cat else None,
            "transaction_count": len(transactions),
            "deductible_expenses": deductible_total
        }
    }
