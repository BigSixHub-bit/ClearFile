import uuid
import json
import asyncio
import logging
import os
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Response

from database import db
from config import APP_NAME, STORAGE_URL
from utils.auth import get_current_user
from utils.storage import put_object, get_object, init_storage
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/receipts/upload")
async def upload_receipt(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    if user.get("subscription_plan") == "starter":
        month_start = datetime.now(timezone.utc).replace(day=1)
        receipt_count = await db.receipts.count_documents({
            "user_id": user["id"],
            "created_at": {"$gte": month_start.isoformat()}
        })
        if receipt_count >= 10:
            raise HTTPException(status_code=403, detail="Starter plan limited to 10 receipts/month")

    allowed_types = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "application/pdf": "pdf"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Use JPEG, PNG, WebP, or PDF.")

    file_data = await file.read()
    if len(file_data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")

    ext = allowed_types[file.content_type]
    storage_path = f"{APP_NAME}/receipts/{user['id']}/{uuid.uuid4()}.{ext}"

    try:
        result = put_object(storage_path, file_data, file.content_type)
    except Exception as e:
        logger.error(f"Receipt upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload receipt")

    receipt_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "storage_path": result["path"],
        "original_filename": file.filename,
        "content_type": file.content_type,
        "size": result.get("size", len(file_data)),
        "extracted_data": None,
        "transaction_id": None,
        "ocr_status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await db.receipts.insert_one(receipt_doc)
    receipt_doc.pop("_id", None)

    asyncio.create_task(extract_receipt_data(receipt_doc["id"], result["path"], user["id"]))
    return receipt_doc


async def extract_receipt_data(receipt_id: str, storage_path: str, user_id: str):
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        return

    try:
        sk = init_storage()
        if not sk:
            return

        image_url = f"{STORAGE_URL}/objects/{storage_path}"

        chat = LlmChat(
            api_key=api_key,
            system_message="""You are a receipt OCR assistant. Extract the following information from receipts:
            - vendor_name: Name of the store/business
            - date: Date of purchase (YYYY-MM-DD format)
            - total_amount: Total amount paid (number only, no currency symbol)
            - currency: Currency (default NGN for Nigerian Naira)
            - category: Suggested expense category (Rent, Utilities, Transport, Equipment, Marketing, Professional Fees, Subscriptions, Food, Miscellaneous)
            - items: List of items if visible

            Return ONLY a valid JSON object with these fields. If a field cannot be determined, use null."""
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")

        response = await chat.send_message(UserMessage(
            text="Extract data from this receipt image. Return only JSON.",
            image_url=image_url
        ))

        try:
            response_text = response.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            extracted_data = json.loads(response_text.strip())

            await db.receipts.update_one(
                {"id": receipt_id},
                {"$set": {"extracted_data": extracted_data, "ocr_status": "completed"}}
            )

            if extracted_data.get("total_amount") and extracted_data.get("category"):
                tx_doc = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "amount": float(extracted_data["total_amount"]),
                    "type": "expense",
                    "category": extracted_data.get("category", "Miscellaneous"),
                    "description": f"Receipt: {extracted_data.get('vendor_name', 'Unknown vendor')}",
                    "date": extracted_data.get("date") or datetime.now(timezone.utc).isoformat(),
                    "bank_account_id": None,
                    "is_recurring": False,
                    "ai_categorized": True,
                    "flagged": False,
                    "receipt_id": receipt_id,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.transactions.insert_one(tx_doc)
                await db.receipts.update_one(
                    {"id": receipt_id},
                    {"$set": {"transaction_id": tx_doc["id"]}}
                )

            logger.info(f"Receipt OCR completed for {receipt_id}")
        except json.JSONDecodeError:
            await db.receipts.update_one(
                {"id": receipt_id},
                {"$set": {"ocr_status": "failed", "ocr_error": "Failed to parse AI response"}}
            )
    except Exception as e:
        logger.error(f"Receipt OCR failed: {e}")
        await db.receipts.update_one(
            {"id": receipt_id},
            {"$set": {"ocr_status": "failed", "ocr_error": str(e)}}
        )


@router.get("/receipts")
async def get_receipts(user: dict = Depends(get_current_user)):
    return await db.receipts.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)


@router.get("/receipts/{receipt_id}")
async def get_receipt(receipt_id: str, user: dict = Depends(get_current_user)):
    receipt = await db.receipts.find_one({"id": receipt_id, "user_id": user["id"]}, {"_id": 0})
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt


@router.get("/receipts/{receipt_id}/download")
async def download_receipt(receipt_id: str, user: dict = Depends(get_current_user)):
    receipt = await db.receipts.find_one({"id": receipt_id, "user_id": user["id"]})
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    try:
        data, content_type = get_object(receipt["storage_path"])
        return Response(content=data, media_type=receipt.get("content_type", content_type))
    except Exception as e:
        logger.error(f"Receipt download failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to download receipt")
