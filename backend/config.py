import os

# JWT
JWT_ALGORITHM = "HS256"

def get_jwt_secret() -> str:
    return os.environ["JWT_SECRET"]

# Paystack
PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY", "")
PAYSTACK_PUBLIC_KEY = os.environ.get("PAYSTACK_PUBLIC_KEY", "")

# Mono
MONO_SECRET_KEY = os.environ.get("MONO_SECRET_KEY", "")
MONO_PUBLIC_KEY = os.environ.get("MONO_PUBLIC_KEY", "")
MONO_WEBHOOK_SECRET = os.environ.get("MONO_WEBHOOK_SECRET", "")
MONO_API_BASE = "https://api.withmono.com/v2"

# Resend Email
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

# Cookies: Secure flag when served over HTTPS
COOKIE_SECURE = FRONTEND_URL.startswith("https")

# Storage
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = "clearfileng"

# Subscription Prices (kobo)
SUBSCRIPTION_PRICES = {
    "bank_connect": 250000,
    "sme_starter": 800000,
    "sme_pro": 1800000,
}

FILING_PRICES = {
    "self_file": 5000,
    "sme_filing": 12000,
}

# AI Models (Section 3 — env-driven, never hardcode)
ANTHROPIC_MODEL_FAST = os.environ.get("ANTHROPIC_MODEL_FAST", "claude-sonnet-5")
ANTHROPIC_MODEL_DEEP = os.environ.get("ANTHROPIC_MODEL_DEEP", "claude-fable-5")

# Nigerian Tax Rates — Nigeria Tax Act (NTA) 2025, effective Jan 1 2026
NTA_PIT_BANDS = [
    (800000, 0.0),
    (2200000, 0.15),
    (9000000, 0.18),
    (12000000, 0.21),
    (36000000, 0.24),
    (float('inf'), 0.25)
]

CIT_RATE_SMALL = 0.0
CIT_RATE_MEDIUM = 0.20
CIT_RATE_LARGE = 0.30
VAT_RATE = 0.075
VAT_EXEMPTION_TURNOVER = 25000000

WHT_RATES = {
    "dividends": 0.10,
    "interest": 0.10,
    "rent": 0.10,
    "royalties": 0.10,
    "professional_fees": 0.10,
    "contracts": 0.05
}

EXPENSE_CATEGORIES = [
    "Salaries", "Rent", "Utilities", "Transport", "Equipment",
    "Marketing", "Professional Fees", "Subscriptions", "Miscellaneous"
]

INCOME_CATEGORIES = [
    "Sales", "Services", "Consulting", "Rent Received", "Transfers In", "Other"
]

NIGERIAN_BANKS = [
    "GTBank", "Access Bank", "Zenith Bank", "First Bank", "UBA",
    "Kuda", "Opay", "Moniepoint", "Sterling Bank", "Stanbic IBTC"
]
