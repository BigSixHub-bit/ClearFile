import uuid
import os
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from database import db
from models import ChatMessage
from utils.auth import get_current_user
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat")
async def chat_with_assistant(message: ChatMessage, user: dict = Depends(get_current_user)):
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")

    session_id = message.session_id or f"nairatrack-{user['id']}-{uuid.uuid4()}"

    system_message = f"""You are NairaTrack Tax Assistant, an expert on Nigerian tax laws and financial management.
    You help Nigerian freelancers, SMEs, and companies understand:
    - Personal Income Tax (PITA) rates (7% to 24% progressive)
    - Company Income Tax (CITA) at 20% for small companies (<N25M) or 30% for larger ones
    - VAT at 7.5%
    - Withholding Tax (WHT) rates
    - FIRS filing requirements and deadlines
    - Tax-deductible expenses
    - Finance Act 2023/2024 changes

    The user is a {user.get('business_type', 'freelancer')} with subscription plan: {user.get('subscription_plan', 'starter')}.

    Be friendly, clear, and use simple language. If asked, you can respond in Nigerian Pidgin.
    Always include practical examples with Naira amounts (N).
    Add disclaimer for complex tax situations to consult a certified tax professional."""

    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=system_message
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")

        user_message = UserMessage(text=message.message)
        response = await chat.send_message(user_message)

        await db.chat_history.insert_one({
            "user_id": user["id"],
            "session_id": session_id,
            "user_message": message.message,
            "assistant_response": response,
            "created_at": datetime.now(timezone.utc).isoformat()
        })

        return {"response": response, "session_id": session_id}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get AI response")


@router.get("/chat/history")
async def get_chat_history(session_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {"user_id": user["id"]}
    if session_id:
        query["session_id"] = session_id
    return await db.chat_history.find(query, {"_id": 0}).sort("created_at", -1).to_list(50)
