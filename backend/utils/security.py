"""Security helpers: rate limiting, client IP, login anomaly signals."""
import logging
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Request

from database import db

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def rate_limit(action: str, limit: int, window_seconds: int, key: str):
    """Mongo-backed fixed-window rate limiter. Raises 429 when exceeded."""
    rl_key = f"{action}:{key}"
    now = datetime.now(timezone.utc)
    doc = await db.rate_limits.find_one({"key": rl_key})
    if doc:
        window_start = datetime.fromisoformat(doc["window_start"])
        if window_start + timedelta(seconds=window_seconds) > now:
            if doc.get("count", 0) >= limit:
                retry_after = int((window_start + timedelta(seconds=window_seconds) - now).total_seconds())
                logger.warning(f"Rate limit exceeded: {action} key={key[:30]}")
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later.",
                    headers={"Retry-After": str(max(retry_after, 1))}
                )
            await db.rate_limits.update_one({"key": rl_key}, {"$inc": {"count": 1}})
            return
    await db.rate_limits.update_one(
        {"key": rl_key},
        {"$set": {
            "window_start": now.isoformat(),
            "count": 1,
            "expires_at": now + timedelta(seconds=window_seconds * 2)
        }},
        upsert=True
    )


async def record_login_event(user_id: str, request: Request):
    """Record login history; notify user on login from a new IP (lightweight suspicious-session signal)."""
    ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")[:200]
    last = await db.login_history.find_one({"user_id": user_id}, sort=[("created_at", -1)])
    await db.login_history.insert_one({
        "user_id": user_id,
        "ip": ip,
        "user_agent": user_agent,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    if last and last.get("ip") and last["ip"] != ip:
        from routes.notifications import create_notification
        await create_notification(
            user_id,
            "New login detected",
            "Your account was accessed from a new location or device. If this wasn't you, reset your password immediately from Settings.",
            "security"
        )
