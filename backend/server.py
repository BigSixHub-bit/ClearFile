from dotenv import load_dotenv
load_dotenv()

import os
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware

from database import db
from utils.auth import hash_password
from utils.storage import init_storage

# Import route modules
from routes.auth import router as auth_router
from routes.transactions import router as transactions_router
from routes.dashboard import router as dashboard_router
from routes.receipts import router as receipts_router
from routes.exports import router as exports_router
from routes.chat import router as chat_router
from routes.education import router as education_router
from routes.payments import router as payments_router
from routes.banking import router as banking_router
from routes.team import router as team_router
from routes.notifications import router as notifications_router
from routes.insights import router as insights_router
from routes.tax_engine import router as tax_engine_router
from routes.whatsapp import router as whatsapp_router

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create the main app
app = FastAPI(title="ClearFile NG API", description="Nigerian Tax & Expense Management")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Include all route modules
api_router.include_router(auth_router)
api_router.include_router(transactions_router)
api_router.include_router(dashboard_router)
api_router.include_router(receipts_router)
api_router.include_router(exports_router)
api_router.include_router(chat_router)
api_router.include_router(education_router)
api_router.include_router(payments_router)
api_router.include_router(banking_router)
api_router.include_router(team_router)
api_router.include_router(notifications_router)
api_router.include_router(insights_router)
api_router.include_router(tax_engine_router)
api_router.include_router(whatsapp_router)


# Health check endpoints
@api_router.get("/")
async def root():
    return {"message": "ClearFile NG API is running", "version": "2.0.0"}


@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


# Include the router in the main app
app.include_router(api_router)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[os.environ.get('FRONTEND_URL', 'http://localhost:3000'), "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.login_attempts.create_index("identifier")
    await db.transactions.create_index([("user_id", 1), ("date", -1)])
    await db.transactions.create_index([("user_id", 1), ("type", 1), ("date", -1)])
    await db.bank_accounts.create_index("user_id")
    await db.receipts.create_index("user_id")
    await db.chat_history.create_index([("user_id", 1), ("session_id", 1)])
    await db.notifications.create_index([("user_id", 1), ("created_at", -1)])

    # Initialize storage
    try:
        init_storage()
        logger.info("Storage initialized successfully")
    except Exception as e:
        logger.warning(f"Storage init warning: {e}")

    # Seed admin user
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@clearfileng.ng")
    admin_password = os.environ.get("ADMIN_PASSWORD", "ClearFile NG2024!")
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "name": "Admin",
            "business_type": "company",
            "monthly_income_range": "1000000+",
            "subscription_plan": "business",
            "onboarding_completed": True,
            "pidgin_mode": False,
            "role": "admin",
            "email_verified": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Admin user created: {admin_email}")

    # Write test credentials
    from pathlib import Path
    Path("/app/memory").mkdir(parents=True, exist_ok=True)
    with open("/app/memory/test_credentials.md", "w") as f:
        f.write(f"""# ClearFile NG Test Credentials

## Admin Account
- Email: {admin_email}
- Password: {admin_password}
- Role: admin
- Plan: Business

## Test User (create via registration)
- Register with any email/password
- Default plan: Starter

## API Endpoints
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/me
- GET /api/dashboard
- GET /api/transactions
- POST /api/transactions
- GET /api/bank-accounts
- POST /api/bank-accounts
- GET /api/tax-calculation
- POST /api/chat
- POST /api/receipts/upload
- GET /api/insights/recurring
- GET /api/insights/spending
""")

    logger.info("ClearFile NG API v2.0 started successfully (modular architecture)")


@app.on_event("shutdown")
async def shutdown_db_client():
    from database import client
    client.close()
