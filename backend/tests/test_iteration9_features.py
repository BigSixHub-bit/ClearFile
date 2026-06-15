"""Tests for iteration 9: duplicate detection, transaction memory, invoices, bank balance, whatsapp settings."""
import os
import time
import uuid
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://tax-naira.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@clearfileng.com"
ADMIN_PASSWORD = "ClearFileNG2024!"


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=20)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text[:200]}"
    return s


# ---------- DUPLICATE DETECTION ----------
class TestDuplicateDetection:
    def test_create_first_tx(self, admin_session):
        payload = {
            "amount": 50000,
            "type": "expense",
            "category": "Rent",
            "description": f"TEST_DUP Sent 50k to 0987654321 {uuid.uuid4().hex[:6]}",
            "date": "2026-01-10T10:00:00+00:00",
            "counterparty_account": "0987654321"
        }
        r = admin_session.post(f"{BASE_URL}/api/transactions", json=payload, timeout=15)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        # First insertion - must not be flagged as duplicate
        assert not data.get("duplicate_skipped"), f"Unexpected dup_skipped: {data}"
        assert data.get("amount") == 50000

    def test_create_duplicate_skipped_or_merged(self, admin_session):
        # Same amount, near same time, similar description
        payload = {
            "amount": 50000,
            "type": "expense",
            "category": "Rent",
            "description": "TEST_DUP Sent 50k to 0987654321 for rent",  # more detail
            "date": "2026-01-10T11:00:00+00:00",
            "counterparty_account": "0987654321"
        }
        r = admin_session.post(f"{BASE_URL}/api/transactions", json=payload, timeout=15)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert data.get("duplicate_skipped") or data.get("duplicate_merged"), f"Expected duplicate flag: {data}"

    def test_get_duplicates_list(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/transactions/duplicates", timeout=20)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert "duplicates" in data
        assert "count" in data
        assert isinstance(data["duplicates"], list)

    def test_cleanup_duplicates(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/transactions/cleanup-duplicates", timeout=20)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert "removed" in data
        assert isinstance(data["removed"], int)


# ---------- TRANSACTION MEMORY ----------
class TestTransactionMemory:
    def test_get_memory(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/transaction-memory", timeout=15)
        assert r.status_code == 200, r.text[:300]
        assert isinstance(r.json(), list)

    def test_check_memory(self, admin_session):
        r = admin_session.get(
            f"{BASE_URL}/api/transaction-memory/check",
            params={"counterparty_account": "0987654321"},
            timeout=15)
        assert r.status_code == 200, r.text[:300]
        body = r.json()
        assert "found" in body

    def test_delete_nonexistent_memory(self, admin_session):
        r = admin_session.delete(f"{BASE_URL}/api/transaction-memory/non-existent-id-123", timeout=15)
        assert r.status_code == 404


# ---------- INVOICES ----------
created_invoice_id = {}

class TestInvoices:
    def test_create_invoice_with_vat(self, admin_session):
        payload = {
            "customer_name": "TEST_Customer Co.",
            "customer_phone": "+2348012345678",
            "items": [
                {"description": "Consulting service", "quantity": 2, "unit_price": 50000},
                {"description": "Hardware", "quantity": 1, "unit_price": 25000}
            ],
            "vat_enabled": True
        }
        r = admin_session.post(f"{BASE_URL}/api/invoices", json=payload, timeout=15)
        assert r.status_code == 200, r.text[:300]
        inv = r.json()
        assert inv["customer_name"] == "TEST_Customer Co."
        assert inv["subtotal"] == 125000
        assert inv["vat_amount"] == round(125000 * 0.075, 2)
        assert inv["total_amount"] == 125000 + inv["vat_amount"]
        assert inv["invoice_number"].startswith("INV-")
        assert inv["status"] == "unpaid"
        assert len(inv["items"]) == 2
        assert inv["items"][0]["line_total"] == 100000
        created_invoice_id["id"] = inv["id"]

    def test_create_invoice_no_vat(self, admin_session):
        payload = {
            "customer_name": "TEST_NoVat Ltd",
            "items": [{"description": "Service", "quantity": 1, "unit_price": 10000}],
            "vat_enabled": False
        }
        r = admin_session.post(f"{BASE_URL}/api/invoices", json=payload, timeout=15)
        assert r.status_code == 200
        inv = r.json()
        assert inv["vat_amount"] == 0
        assert inv["total_amount"] == 10000

    def test_create_invoice_missing_customer(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/invoices",
                               json={"items": [{"quantity": 1, "unit_price": 100}]}, timeout=15)
        assert r.status_code == 400

    def test_create_invoice_zero_total(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/invoices",
                               json={"customer_name": "X", "items": []}, timeout=15)
        assert r.status_code == 400

    def test_list_invoices(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/invoices", timeout=15)
        assert r.status_code == 200
        invs = r.json()
        assert isinstance(invs, list)
        assert len(invs) >= 1
        ids = [i["id"] for i in invs]
        assert created_invoice_id["id"] in ids

    def test_get_invoice_detail(self, admin_session):
        iid = created_invoice_id.get("id")
        r = admin_session.get(f"{BASE_URL}/api/invoices/{iid}", timeout=15)
        assert r.status_code == 200
        inv = r.json()
        assert inv["id"] == iid

    def test_update_invoice_status_paid(self, admin_session):
        iid = created_invoice_id.get("id")
        r = admin_session.put(f"{BASE_URL}/api/invoices/{iid}/status",
                              json={"status": "paid"}, timeout=15)
        assert r.status_code == 200
        # Verify persisted
        r2 = admin_session.get(f"{BASE_URL}/api/invoices/{iid}", timeout=15)
        assert r2.status_code == 200
        assert r2.json()["status"] == "paid"
        assert r2.json().get("paid_date") is not None

    def test_update_invoice_invalid_status(self, admin_session):
        iid = created_invoice_id.get("id")
        r = admin_session.put(f"{BASE_URL}/api/invoices/{iid}/status",
                              json={"status": "garbage"}, timeout=15)
        assert r.status_code == 400


# ---------- DASHBOARD BANK BALANCE ----------
class TestDashboardBankBalance:
    def test_dashboard_has_bank_balance_fields(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/dashboard", timeout=20)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert "total_bank_balance" in d
        assert "has_linked_bank" in d
        assert isinstance(d["has_linked_bank"], bool)
        # Should be non-zero given admin has transactions
        assert isinstance(d["total_bank_balance"], (int, float))


# ---------- WHATSAPP SETTINGS ----------
class TestWhatsAppSettings:
    def test_get_default_settings(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/whatsapp/settings", timeout=15)
        assert r.status_code == 200, r.text[:300]
        s = r.json()
        for k in ("transaction_notifications", "weekly_summary", "tax_reminders"):
            assert k in s, f"Missing field {k}: {s}"

    def test_update_settings(self, admin_session):
        new_vals = {"transaction_notifications": False, "weekly_summary": True, "tax_reminders": False}
        r = admin_session.put(f"{BASE_URL}/api/whatsapp/settings", json=new_vals, timeout=15)
        assert r.status_code == 200, r.text[:300]
        # Verify
        r2 = admin_session.get(f"{BASE_URL}/api/whatsapp/settings", timeout=15)
        s = r2.json()
        assert s["transaction_notifications"] is False
        assert s["tax_reminders"] is False
        assert s["weekly_summary"] is True
        # Restore defaults
        admin_session.put(f"{BASE_URL}/api/whatsapp/settings",
                          json={"transaction_notifications": True, "weekly_summary": True, "tax_reminders": True},
                          timeout=15)
