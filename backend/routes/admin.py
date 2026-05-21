"""Admin Panel - Expert request management, user management, dashboard stats"""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request
from bson import ObjectId

from database import db
from utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin")


async def require_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ========================
# ADMIN DASHBOARD STATS
# ========================

@router.get("/stats")
async def get_admin_stats(user: dict = Depends(require_admin)):
    total_users = await db.users.count_documents({})
    total_transactions = await db.transactions.count_documents({})
    total_expert_requests = await db.expert_requests.count_documents({})
    pending_requests = await db.expert_requests.count_documents({"status": "pending"})
    matched_requests = await db.expert_requests.count_documents({"status": "matched"})
    completed_requests = await db.expert_requests.count_documents({"status": "completed"})

    plan_counts = {}
    for plan in ["starter", "pro", "growth", "business"]:
        plan_counts[plan] = await db.users.count_documents({"subscription_plan": plan})

    return {
        "total_users": total_users,
        "total_transactions": total_transactions,
        "expert_requests": {
            "total": total_expert_requests,
            "pending": pending_requests,
            "matched": matched_requests,
            "completed": completed_requests
        },
        "plan_breakdown": plan_counts
    }


# ========================
# EXPERT REQUEST MANAGEMENT
# ========================

@router.get("/expert-requests")
async def list_expert_requests(
    status: str = None,
    user: dict = Depends(require_admin)
):
    query = {}
    if status:
        query["status"] = status

    requests = await db.expert_requests.find(query, {"_id": 0}).sort("created_at", -1).limit(100).to_list(100)
    return {"requests": requests, "count": len(requests)}


@router.put("/expert-requests/{request_id}/status")
async def update_request_status(request_id: str, request: Request, user: dict = Depends(require_admin)):
    data = await request.json()
    new_status = data.get("status")

    if new_status not in ["pending", "reviewing", "matched", "in_progress", "completed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    update_fields = {
        "status": new_status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": user["id"]
    }

    if new_status == "matched":
        update_fields["matched_at"] = datetime.now(timezone.utc).isoformat()
        expert_name = data.get("expert_name", "")
        expert_email = data.get("expert_email", "")
        if expert_name:
            update_fields["matched_expert"] = {
                "name": expert_name,
                "email": expert_email,
                "phone": data.get("expert_phone", ""),
                "specialty": data.get("expert_specialty", "")
            }

    result = await db.expert_requests.update_one(
        {"id": request_id},
        {"$set": update_fields}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Request not found")

    # Notify user about status change
    req = await db.expert_requests.find_one({"id": request_id}, {"_id": 0})
    if req:
        status_messages = {
            "reviewing": "Your expert request is being reviewed.",
            "matched": f"Great news! You've been matched with {data.get('expert_name', 'an expert')}. They'll contact you shortly.",
            "in_progress": "Your tax professional is working on your filing.",
            "completed": "Your expert filing request has been completed.",
            "cancelled": "Your expert request has been cancelled."
        }
        import uuid
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": req["user_id"],
            "title": f"Expert Request: {new_status.replace('_', ' ').title()}",
            "message": status_messages.get(new_status, f"Status updated to {new_status}"),
            "type": "info",
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })

    return {"message": f"Status updated to {new_status}", "request_id": request_id}


@router.post("/expert-requests/{request_id}/note")
async def add_admin_note(request_id: str, request: Request, user: dict = Depends(require_admin)):
    data = await request.json()
    note_text = data.get("note", "").strip()
    if not note_text:
        raise HTTPException(status_code=400, detail="Note text required")

    import uuid
    note = {
        "id": str(uuid.uuid4()),
        "text": note_text,
        "admin_id": user["id"],
        "admin_name": user.get("name", "Admin"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    result = await db.expert_requests.update_one(
        {"id": request_id},
        {"$push": {"admin_notes": note}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Request not found")

    return {"message": "Note added", "note": note}


# ========================
# USER MANAGEMENT
# ========================

@router.get("/users")
async def list_users(user: dict = Depends(require_admin)):
    users = []
    async for u in db.users.find({}, {"password_hash": 0}).sort("created_at", -1).limit(100):
        u["id"] = str(u.pop("_id"))
        users.append(u)
    return {"users": users, "count": len(users)}


@router.put("/users/{user_id}/plan")
async def update_user_plan(user_id: str, request: Request, user: dict = Depends(require_admin)):
    data = await request.json()
    plan = data.get("plan")
    if plan not in ["starter", "pro", "growth", "business"]:
        raise HTTPException(status_code=400, detail="Invalid plan")

    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"subscription_plan": plan}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User plan updated to {plan}"}
