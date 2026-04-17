import secrets
import asyncio
import logging
import resend
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from bson import ObjectId

from database import db
from config import RESEND_API_KEY, SENDER_EMAIL, FRONTEND_URL, get_jwt_secret, JWT_ALGORITHM
from models import UserRegister, UserLogin, PasswordResetRequest, PasswordResetConfirm
from utils.auth import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, get_current_user
)

import jwt as pyjwt

logger = logging.getLogger(__name__)

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

router = APIRouter()


@router.post("/auth/register")
async def register(user_data: UserRegister, response: Response):
    email = user_data.email.lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    verification_token = secrets.token_urlsafe(32)
    user_doc = {
        "email": email,
        "password_hash": hash_password(user_data.password),
        "name": user_data.name,
        "business_type": user_data.business_type,
        "monthly_income_range": user_data.monthly_income_range,
        "subscription_plan": "starter",
        "onboarding_completed": False,
        "pidgin_mode": False,
        "email_verified": False,
        "verification_token": verification_token,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)

    if RESEND_API_KEY:
        try:
            verification_url = f"{FRONTEND_URL}/verify-email?token={verification_token}"
            await asyncio.to_thread(resend.Emails.send, {
                "from": SENDER_EMAIL,
                "to": [email],
                "subject": "Verify your NairaTrack account",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: #006400; padding: 20px; text-align: center;">
                        <h1 style="color: white; margin: 0;">NairaTrack</h1>
                    </div>
                    <div style="padding: 30px; background: #f9f9f9;">
                        <h2 style="color: #022c22;">Welcome, {user_data.name}!</h2>
                        <p style="color: #555;">Please verify your email address to complete your registration.</p>
                        <a href="{verification_url}" style="display: inline-block; background: #006400; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; margin: 20px 0;">Verify Email</a>
                        <p style="color: #888; font-size: 12px;">If you didn't create this account, please ignore this email.</p>
                    </div>
                </div>
                """
            })
            logger.info(f"Verification email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")

    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)

    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")

    return {
        "id": user_id, "email": email, "name": user_data.name,
        "business_type": user_data.business_type,
        "monthly_income_range": user_data.monthly_income_range,
        "subscription_plan": "starter", "onboarding_completed": False,
        "pidgin_mode": False, "email_verified": False,
        "created_at": user_doc["created_at"]
    }


@router.post("/auth/login")
async def login(credentials: UserLogin, response: Response, request: Request):
    email = credentials.email.lower()
    identifier = f"{request.client.host}:{email}"

    attempts = await db.login_attempts.find_one({"identifier": identifier})
    if attempts and attempts.get("count", 0) >= 5:
        lockout_time = attempts.get("last_attempt")
        if lockout_time:
            lockout_until = datetime.fromisoformat(lockout_time) + timedelta(minutes=15)
            if datetime.now(timezone.utc) < lockout_until:
                raise HTTPException(status_code=429, detail="Too many failed attempts. Try again in 15 minutes.")
            else:
                await db.login_attempts.delete_one({"identifier": identifier})

    user = await db.users.find_one({"email": email})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {"$inc": {"count": 1}, "$set": {"last_attempt": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        raise HTTPException(status_code=401, detail="Invalid email or password")

    await db.login_attempts.delete_one({"identifier": identifier})

    user_id = str(user["_id"])
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)

    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")

    return {
        "id": user_id, "email": user["email"], "name": user["name"],
        "business_type": user["business_type"],
        "monthly_income_range": user.get("monthly_income_range", "0-100000"),
        "subscription_plan": user.get("subscription_plan", "starter"),
        "onboarding_completed": user.get("onboarding_completed", False),
        "pidgin_mode": user.get("pidgin_mode", False),
        "created_at": user["created_at"]
    }


@router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logged out successfully"}


@router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {
        "id": user["id"], "email": user["email"], "name": user["name"],
        "business_type": user.get("business_type", "freelancer"),
        "monthly_income_range": user.get("monthly_income_range", "0-100000"),
        "subscription_plan": user.get("subscription_plan", "starter"),
        "onboarding_completed": user.get("onboarding_completed", False),
        "pidgin_mode": user.get("pidgin_mode", False),
        "email_verified": user.get("email_verified", False),
        "created_at": user.get("created_at", "")
    }


@router.post("/auth/verify-email")
async def verify_email(request: Request):
    data = await request.json()
    token = data.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Verification token required")

    user = await db.users.find_one({"verification_token": token})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    if user.get("email_verified"):
        return {"message": "Email already verified"}

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"email_verified": True}, "$unset": {"verification_token": ""}}
    )
    return {"message": "Email verified successfully"}


@router.post("/auth/resend-verification")
async def resend_verification(user: dict = Depends(get_current_user)):
    if user.get("email_verified"):
        return {"message": "Email already verified"}
    if not RESEND_API_KEY:
        raise HTTPException(status_code=400, detail="Email service not configured")

    verification_token = secrets.token_urlsafe(32)
    await db.users.update_one(
        {"_id": ObjectId(user["id"])},
        {"$set": {"verification_token": verification_token}}
    )

    try:
        verification_url = f"{FRONTEND_URL}/verify-email?token={verification_token}"
        await asyncio.to_thread(resend.Emails.send, {
            "from": SENDER_EMAIL,
            "to": [user["email"]],
            "subject": "Verify your NairaTrack account",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: #006400; padding: 20px; text-align: center;">
                    <h1 style="color: white; margin: 0;">NairaTrack</h1>
                </div>
                <div style="padding: 30px; background: #f9f9f9;">
                    <h2 style="color: #022c22;">Verify Your Email</h2>
                    <p style="color: #555;">Click the button below to verify your email address.</p>
                    <a href="{verification_url}" style="display: inline-block; background: #006400; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; margin: 20px 0;">Verify Email</a>
                </div>
            </div>
            """
        })
        return {"message": "Verification email sent"}
    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send verification email")


@router.post("/auth/forgot-password")
async def forgot_password(data: PasswordResetRequest):
    email = data.email.lower()
    user = await db.users.find_one({"email": email})
    if not user:
        return {"message": "If an account exists, a password reset email will be sent"}

    reset_token = secrets.token_urlsafe(32)
    reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"reset_token": reset_token, "reset_expires": reset_expires.isoformat()}}
    )

    if RESEND_API_KEY:
        try:
            reset_url = f"{FRONTEND_URL}/reset-password?token={reset_token}"
            await asyncio.to_thread(resend.Emails.send, {
                "from": SENDER_EMAIL,
                "to": [email],
                "subject": "Reset your NairaTrack password",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: #006400; padding: 20px; text-align: center;">
                        <h1 style="color: white; margin: 0;">NairaTrack</h1>
                    </div>
                    <div style="padding: 30px; background: #f9f9f9;">
                        <h2 style="color: #022c22;">Reset Your Password</h2>
                        <p style="color: #555;">Click the button below to reset your password. This link expires in 1 hour.</p>
                        <a href="{reset_url}" style="display: inline-block; background: #006400; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; margin: 20px 0;">Reset Password</a>
                        <p style="color: #888; font-size: 12px;">If you didn't request this, please ignore this email.</p>
                    </div>
                </div>
                """
            })
            logger.info(f"Password reset email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send reset email: {e}")

    return {"message": "If an account exists, a password reset email will be sent"}


@router.post("/auth/reset-password")
async def reset_password(data: PasswordResetConfirm):
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    user = await db.users.find_one({"reset_token": data.token})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    expires = user.get("reset_expires")
    if expires:
        expires_dt = datetime.fromisoformat(expires)
        if datetime.now(timezone.utc) > expires_dt:
            raise HTTPException(status_code=400, detail="Reset token has expired")

    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"password_hash": hash_password(data.new_password)},
            "$unset": {"reset_token": "", "reset_expires": ""}
        }
    )
    return {"message": "Password reset successfully"}


@router.post("/auth/refresh")
async def refresh_token(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    try:
        payload = pyjwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        user_id = str(user["_id"])
        access_token = create_access_token(user_id, user["email"])
        response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
        return {"message": "Token refreshed"}
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.put("/user/settings")
async def update_settings(request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    update_fields = {}
    for field in ["pidgin_mode", "onboarding_completed", "business_type", "monthly_income_range"]:
        if field in data:
            update_fields[field] = data[field]
    if update_fields:
        await db.users.update_one({"_id": ObjectId(user["id"])}, {"$set": update_fields})
    return {"message": "Settings updated"}


@router.put("/user/subscription")
async def update_subscription(request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    plan = data.get("plan")
    if plan not in ["starter", "growth", "business"]:
        raise HTTPException(status_code=400, detail="Invalid subscription plan")
    await db.users.update_one(
        {"_id": ObjectId(user["id"])},
        {"$set": {"subscription_plan": plan}}
    )
    return {"message": f"Subscription updated to {plan}"}
