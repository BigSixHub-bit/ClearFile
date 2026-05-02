import uuid
import secrets
import asyncio
import logging
import resend
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request

from database import db
from config import RESEND_API_KEY, SENDER_EMAIL, FRONTEND_URL
from models import TeamMemberInvite
from utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/team/invite")
async def invite_team_member(data: TeamMemberInvite, user: dict = Depends(get_current_user)):
    if user.get("subscription_plan") != "business":
        raise HTTPException(status_code=403, detail="Multi-user access requires Business plan")

    existing = await db.team_members.find_one({
        "owner_id": user["id"],
        "email": data.email.lower()
    })
    if existing:
        raise HTTPException(status_code=400, detail="User already invited")

    invite_token = secrets.token_urlsafe(32)

    team_member = {
        "id": str(uuid.uuid4()),
        "owner_id": user["id"],
        "owner_email": user["email"],
        "email": data.email.lower(),
        "role": data.role,
        "status": "pending",
        "invite_token": invite_token,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await db.team_members.insert_one(team_member)

    if RESEND_API_KEY:
        try:
            invite_url = f"{FRONTEND_URL}/team/accept?token={invite_token}"
            await asyncio.to_thread(resend.Emails.send, {
                "from": SENDER_EMAIL,
                "to": [data.email],
                "subject": f"You've been invited to join {user['name']}'s ClearFile NG account",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: #006400; padding: 20px; text-align: center;">
                        <h1 style="color: white; margin: 0;">ClearFile NG</h1>
                    </div>
                    <div style="padding: 30px; background: #f9f9f9;">
                        <h2 style="color: #022c22;">Team Invitation</h2>
                        <p style="color: #555;">{user['name']} has invited you to access their ClearFile NG account as a {data.role}.</p>
                        <a href="{invite_url}" style="display: inline-block; background: #006400; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; margin: 20px 0;">Accept Invitation</a>
                    </div>
                </div>
                """
            })
        except Exception as e:
            logger.error(f"Failed to send team invite email: {e}")

    team_member.pop("_id", None)
    team_member.pop("invite_token", None)
    return team_member


@router.get("/team/members")
async def get_team_members(user: dict = Depends(get_current_user)):
    if user.get("subscription_plan") != "business":
        raise HTTPException(status_code=403, detail="Multi-user access requires Business plan")
    return await db.team_members.find(
        {"owner_id": user["id"]},
        {"_id": 0, "invite_token": 0}
    ).to_list(50)


@router.post("/team/accept")
async def accept_team_invite(request: Request):
    data = await request.json()
    token = data.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Invite token required")

    invite = await db.team_members.find_one({"invite_token": token})
    if not invite:
        raise HTTPException(status_code=400, detail="Invalid or expired invitation")

    if invite["status"] != "pending":
        return {"message": "Invitation already accepted"}

    await db.team_members.update_one(
        {"invite_token": token},
        {"$set": {"status": "active"}, "$unset": {"invite_token": ""}}
    )
    return {"message": "Invitation accepted", "owner_email": invite["owner_email"]}


@router.delete("/team/members/{member_id}")
async def remove_team_member(member_id: str, user: dict = Depends(get_current_user)):
    result = await db.team_members.delete_one({"id": member_id, "owner_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Team member not found")
    return {"message": "Team member removed"}
