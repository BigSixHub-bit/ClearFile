"""ClearFile NG - Iteration 10 Security Hardening Tests"""
import os
import time
import uuid
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://tax-naira.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@clearfileng.com"
ADMIN_PASSWORD = "ClearFileNG2024!"


def _new_email():
    return f"test_{uuid.uuid4().hex[:10]}@clearfiletest.com"


@pytest.fixture
def admin_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture
def user_session():
    s = requests.Session()
    email = _new_email()
    r = s.post(f"{API}/auth/register", json={
        "email": email, "password": "StrongPass123", "name": "Test User", "business_name": "TB"
    }, timeout=15)
    if r.status_code == 429:
        pytest.skip("Registration rate limit hit")
    assert r.status_code in (200, 201), f"Register failed: {r.status_code} {r.text}"
    return s, email


# ---------- REGRESSION ----------
class TestRegression:
    def test_admin_login_and_endpoints(self, admin_session):
        for path in ["/auth/me", "/dashboard", "/transactions", "/invoices"]:
            r = admin_session.get(f"{API}{path}", timeout=15)
            assert r.status_code == 200, f"{path} -> {r.status_code}"

    def test_user_register_login_transaction_invoice(self, user_session):
        s, email = user_session
        me = s.get(f"{API}/auth/me", timeout=15)
        assert me.status_code == 200
        # create a transaction
        tx = s.post(f"{API}/transactions", json={
            "amount": 1500, "type": "income", "category": "sales",
            "description": "Test sale", "date": "2026-01-15"
        }, timeout=15)
        assert tx.status_code in (200, 201), tx.text
        # list
        lst = s.get(f"{API}/transactions", timeout=15)
        assert lst.status_code == 200
        # create invoice
        inv = s.post(f"{API}/invoices", json={
            "customer_name": "Client A",
            "items": [{"description": "Service", "quantity": 1, "unit_price": 1000}],
            "due_date": "2026-02-15"
        }, timeout=15)
        assert inv.status_code in (200, 201), inv.text


# ---------- SECURITY ----------
class TestSecurity:
    def test_register_short_password(self):
        r = requests.post(f"{API}/auth/register", json={
            "email": _new_email(), "password": "short", "name": "X", "business_name": "Y"
        }, timeout=15)
        assert r.status_code in (400, 422), f"got {r.status_code}: {r.text}"

    def test_subscription_upgrade_blocked(self, user_session):
        s, _ = user_session
        for plan in ["business", "pro"]:
            r = s.put(f"{API}/user/subscription", json={"plan": plan}, timeout=15)
            assert r.status_code == 403, f"plan {plan} -> {r.status_code}"
        r = s.put(f"{API}/user/subscription", json={"plan": "starter"}, timeout=15)
        assert r.status_code == 200, f"starter -> {r.status_code} {r.text}"

    def test_unauthenticated_401(self):
        for path in ["/auth/me", "/dashboard", "/transactions", "/invoices"]:
            r = requests.get(f"{API}{path}", timeout=15)
            assert r.status_code == 401, f"{path} -> {r.status_code}"

    def test_admin_endpoints_forbidden_for_user(self, user_session):
        s, _ = user_session
        for path in ["/admin/stats", "/admin/users"]:
            r = s.get(f"{API}{path}", timeout=15)
            assert r.status_code == 403, f"{path} -> {r.status_code}"

    def test_security_headers(self):
        r = requests.get(f"{API}/auth/me", timeout=15)
        h = {k.lower(): v for k, v in r.headers.items()}
        assert h.get("x-content-type-options", "").lower() == "nosniff"
        assert h.get("x-frame-options", "").upper() == "DENY"
        assert "strict-transport-security" in h

    def test_idor_transaction(self):
        # user A
        a = requests.Session()
        ea = _new_email()
        ra = a.post(f"{API}/auth/register", json={"email": ea, "password": "StrongPass123", "name": "A", "business_name": "A"}, timeout=15)
        if ra.status_code == 429:
            pytest.skip("rate limit")
        assert ra.status_code in (200, 201)
        tx = a.post(f"{API}/transactions", json={
            "amount": 500, "type": "income", "category": "sales", "description": "A tx", "date": "2026-01-15"
        }, timeout=15)
        assert tx.status_code in (200, 201)
        tx_id = tx.json().get("id") or tx.json().get("_id") or tx.json().get("transaction", {}).get("id")
        assert tx_id, f"no tx id: {tx.json()}"

        # user B
        b = requests.Session()
        eb = _new_email()
        rb = b.post(f"{API}/auth/register", json={"email": eb, "password": "StrongPass123", "name": "B", "business_name": "B"}, timeout=15)
        if rb.status_code == 429:
            pytest.skip("rate limit")
        assert rb.status_code in (200, 201)

        g = b.put(f"{API}/transactions/{tx_id}", json={"description": "hacked"}, timeout=15)
        # update is scoped by user_id so returns 200 but no change (safe)
        assert g.status_code in (200, 403, 404), f"IDOR PUT -> {g.status_code}"
        d = b.delete(f"{API}/transactions/{tx_id}", timeout=15)
        assert d.status_code in (403, 404), f"IDOR DELETE -> {d.status_code}"
        # verify A still sees tx with original description
        ga = a.get(f"{API}/transactions", timeout=15)
        assert ga.status_code == 200
        txs = ga.json() if isinstance(ga.json(), list) else ga.json().get("transactions", [])
        found = [t for t in txs if t.get("id") == tx_id]
        assert found, "owner lost tx"
        assert found[0].get("description") == "A tx", f"IDOR allowed update! {found[0]}"

    def test_idor_invoice(self):
        a = requests.Session()
        ea = _new_email()
        ra = a.post(f"{API}/auth/register", json={"email": ea, "password": "StrongPass123", "name": "A", "business_name": "A"}, timeout=15)
        if ra.status_code == 429:
            pytest.skip("rate limit")
        inv = a.post(f"{API}/invoices", json={
            "customer_name": "C",
            "items": [{"description": "s", "quantity": 1, "unit_price": 100}],
            "due_date": "2026-02-15"
        }, timeout=15)
        assert inv.status_code in (200, 201), inv.text
        inv_id = inv.json().get("id") or inv.json().get("_id")
        assert inv_id

        b = requests.Session()
        eb = _new_email()
        rb = b.post(f"{API}/auth/register", json={"email": eb, "password": "StrongPass123", "name": "B", "business_name": "B"}, timeout=15)
        if rb.status_code == 429:
            pytest.skip("rate limit")
        g = b.get(f"{API}/invoices/{inv_id}", timeout=15)
        assert g.status_code in (403, 404), f"IDOR invoice -> {g.status_code}"

    def test_brute_force_lockout(self):
        email = _new_email()
        s = requests.Session()
        r = s.post(f"{API}/auth/register", json={"email": email, "password": "StrongPass123", "name": "L", "business_name": "L"}, timeout=15)
        if r.status_code == 429:
            pytest.skip("register rate limit")
        statuses = []
        for _ in range(7):
            rr = requests.post(f"{API}/auth/login", json={"email": email, "password": "WrongPass!!"}, timeout=15)
            statuses.append(rr.status_code)
            if rr.status_code == 429:
                break
        assert 429 in statuses, f"no lockout observed: {statuses}"


# ---------- PUBLIC files ----------
class TestPublicAssets:
    def test_robots(self):
        r = requests.get(f"{BASE_URL}/robots.txt", timeout=15)
        assert r.status_code == 200
        assert "User-agent" in r.text or "Disallow" in r.text or "Sitemap" in r.text

    def test_sitemap(self):
        r = requests.get(f"{BASE_URL}/sitemap.xml", timeout=15)
        assert r.status_code == 200
        assert "<urlset" in r.text or "<sitemap" in r.text
