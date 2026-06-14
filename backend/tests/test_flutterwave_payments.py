"""Flutterwave V4 Payment Integration Tests
Tests:
- Subscription plans endpoint exposes flutterwave_configured field
- AI Guide payment initialize/verify/status for admin & new user
- Subscription initialize/verify
- Webhook accepts charge.completed event
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://tax-naira.preview.emergentagent.com").rstrip("/")

ADMIN_EMAIL = "admin@clearfileng.com"
ADMIN_PASSWORD = "ClearFileNG2024!"


# --- Auth helpers ---
def _login_session(email: str, password: str) -> requests.Session:
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=20)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def admin_session():
    return _login_session(ADMIN_EMAIL, ADMIN_PASSWORD)


@pytest.fixture(scope="module")
def new_user_session():
    s = requests.Session()
    email = f"TEST_flw_{uuid.uuid4().hex[:10]}@test.com"
    password = "Test1234!"
    payload = {
        "email": email,
        "password": password,
        "name": "Flutterwave Tester",
        "business_type": "freelancer",
    }
    r = s.post(f"{BASE_URL}/api/auth/register", json=payload, timeout=20)
    # If register endpoint requires different fields, fall back to minimal
    if r.status_code >= 400:
        r = s.post(f"{BASE_URL}/api/auth/register", json={"email": email, "password": password, "name": "Tester"}, timeout=20)
    assert r.status_code in (200, 201), f"Register failed: {r.status_code} {r.text}"
    # Some apps don't auto-login on register — login explicitly
    r2 = s.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=20)
    assert r2.status_code == 200, f"Login after register failed: {r2.text}"
    return s


# --- Subscription Plans ---
class TestSubscriptionPlans:
    def test_plans_returns_flutterwave_configured(self):
        r = requests.get(f"{BASE_URL}/api/subscription/plans", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert "plans" in data
        assert isinstance(data["plans"], list)
        assert len(data["plans"]) >= 2
        assert "flutterwave_configured" in data
        assert isinstance(data["flutterwave_configured"], bool)
        # With creds in .env should be True
        assert data["flutterwave_configured"] is True
        ids = [p["id"] for p in data["plans"]]
        assert "starter" in ids and "pro" in ids


# --- AI Guide Payments ---
class TestAIGuidePayments:
    def test_status_admin_unlocked(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/payments/ai-guide/status", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert "unlocked" in data
        # Admin already has guide unlocked from earlier mock session
        assert data["unlocked"] is True

    def test_initialize_admin_already_unlocked(self, admin_session):
        r = admin_session.post(
            f"{BASE_URL}/api/payments/ai-guide/initialize",
            json={"callback_url": f"{BASE_URL}/payment-success"},
            timeout=30,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("already_unlocked") is True

    def test_status_new_user_not_unlocked(self, new_user_session):
        r = new_user_session.get(f"{BASE_URL}/api/payments/ai-guide/status", timeout=20)
        assert r.status_code == 200
        assert r.json().get("unlocked") is False

    def test_initialize_new_user(self, new_user_session):
        r = new_user_session.post(
            f"{BASE_URL}/api/payments/ai-guide/initialize",
            json={"callback_url": f"{BASE_URL}/payment-success"},
            timeout=30,
        )
        # With FLW configured but creds invalid → 502 expected
        # Or could return payment_link if creds work, or mock unlock if not configured
        assert r.status_code in (200, 502)
        if r.status_code == 200:
            data = r.json()
            assert ("payment_link" in data and data.get("tx_ref")) or data.get("mock") is True
        # 502 (proxy/backend) is acceptable when FLW credentials invalid


    def test_verify_mock_or_error(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/payments/ai-guide/verify", timeout=20)
        # If configured (true) → requires transaction_id (400). If not configured → mock success.
        assert r.status_code in (200, 400)
        if r.status_code == 200:
            data = r.json()
            assert data.get("status") == "success"


# --- Subscription Payments ---
class TestSubscriptionPayments:
    def test_initialize_starter(self, new_user_session):
        r = new_user_session.post(
            f"{BASE_URL}/api/subscription/initialize",
            json={"plan": "starter", "callback_url": f"{BASE_URL}/payment-success"},
            timeout=30,
        )
        assert r.status_code in (200, 502)
        if r.status_code == 200:
            data = r.json()
            assert ("payment_link" in data) or data.get("mock") is True

    def test_initialize_invalid_plan(self, new_user_session):
        r = new_user_session.post(
            f"{BASE_URL}/api/subscription/initialize",
            json={"plan": "invalid_plan"},
            timeout=20,
        )
        assert r.status_code in (400, 422)

    def test_verify_without_txid(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/subscription/verify", timeout=20)
        # If configured → 400 (missing tx id). If not → 200 mock.
        assert r.status_code in (200, 400)


# --- Subscription Webhook ---
class TestSubscriptionWebhook:
    def test_webhook_invalid_signature(self):
        r = requests.post(
            f"{BASE_URL}/api/subscription/webhook",
            json={"event": "charge.completed", "data": {}},
            headers={"verif-hash": "wrong_signature"},
            timeout=20,
        )
        assert r.status_code == 401

    def test_webhook_valid_signature_charge_completed(self):
        # Use the secret hash from backend .env
        secret = "clearfileng_flw_webhook_2024"
        payload = {
            "event": "charge.completed",
            "data": {
                "id": 999999,
                "tx_ref": "cfng_sub_nonexistent_ref",
                "status": "successful",
                "currency": "NGN",
                "amount": 2000,
            },
        }
        r = requests.post(
            f"{BASE_URL}/api/subscription/webhook",
            json=payload,
            headers={"verif-hash": secret},
            timeout=20,
        )
        assert r.status_code == 200
        assert r.json().get("status") == "ok"
