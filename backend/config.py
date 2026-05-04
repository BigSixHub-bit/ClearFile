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

# Storage
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = "clearfileng"

# Subscription Prices (kobo)
SUBSCRIPTION_PRICES = {
    "starter": 200000,
    "pro": 400000,
    "growth": 400000,
}

# Nigerian Tax Rates
PITA_RATES = [
    (300000, 0.07),
    (300000, 0.11),
    (500000, 0.15),
    (500000, 0.19),
    (1600000, 0.21),
    (float('inf'), 0.24)
]

CITA_RATE_SMALL = 0.20
CITA_RATE_LARGE = 0.30
VAT_RATE = 0.075

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
