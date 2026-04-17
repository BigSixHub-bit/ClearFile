import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request

from database import db
from utils.auth import get_current_user

router = APIRouter()


async def create_notification(user_id: str, title: str, message: str, notification_type: str = "info"):
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": title,
        "message": message,
        "type": notification_type,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification)
    return notification


@router.get("/notifications")
async def get_notifications(user: dict = Depends(get_current_user)):
    return await db.notifications.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)


@router.post("/notifications/mark-read")
async def mark_notifications_read(request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    notification_ids = data.get("ids", [])

    if notification_ids:
        await db.notifications.update_many(
            {"id": {"$in": notification_ids}, "user_id": user["id"]},
            {"$set": {"read": True}}
        )
    else:
        await db.notifications.update_many(
            {"user_id": user["id"]},
            {"$set": {"read": True}}
        )
    return {"message": "Notifications marked as read"}


@router.get("/notifications/unread-count")
async def get_unread_count(user: dict = Depends(get_current_user)):
    count = await db.notifications.count_documents({
        "user_id": user["id"],
        "read": False
    })
    return {"count": count}


@router.post("/notifications/check-deadlines")
async def check_deadline_notifications(user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    user_id = user["id"]
    notifications_created = []

    # VAT deadline - 21st of each month
    if now.day >= 15 and now.day <= 21:
        existing = await db.notifications.find_one({
            "user_id": user_id,
            "type": "vat_reminder",
            "created_at": {"$gte": now.replace(day=1).isoformat()}
        })
        if not existing:
            notif = await create_notification(
                user_id,
                "VAT Filing Reminder",
                "VAT filing deadline is on the 21st. Make sure to file your VAT returns.",
                "vat_reminder"
            )
            notifications_created.append(notif)

    # Annual returns - March 31
    if now.month == 3 and now.day >= 15:
        existing = await db.notifications.find_one({
            "user_id": user_id,
            "type": "annual_reminder",
            "created_at": {"$gte": now.replace(month=3, day=1).isoformat()}
        })
        if not existing:
            notif = await create_notification(
                user_id,
                "Annual Tax Returns Due",
                "Annual personal income tax returns are due by March 31st.",
                "annual_reminder"
            )
            notifications_created.append(notif)

    # Monthly summary - 1st of each month
    if now.day == 1:
        existing = await db.notifications.find_one({
            "user_id": user_id,
            "type": "monthly_summary",
            "created_at": {"$gte": now.isoformat()}
        })
        if not existing:
            last_month = now - timedelta(days=1)
            month_start = last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            transactions = await db.transactions.find({
                "user_id": user_id,
                "created_at": {"$gte": month_start.isoformat(), "$lt": now.isoformat()}
            }).to_list(1000)

            income = sum(tx["amount"] for tx in transactions if tx["type"] == "income")
            expenses = sum(tx["amount"] for tx in transactions if tx["type"] == "expense")

            notif = await create_notification(
                user_id,
                "Monthly Summary Ready",
                f"Your {last_month.strftime('%B')} summary: N{income:,.0f} income, N{expenses:,.0f} expenses",
                "monthly_summary"
            )
            notifications_created.append(notif)

    return {"notifications_created": len(notifications_created), "notifications": notifications_created}
