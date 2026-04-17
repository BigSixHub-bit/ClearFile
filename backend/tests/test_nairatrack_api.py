#!/usr/bin/env python3
"""
NairaTrack API Tests - Comprehensive Backend Testing
Tests: Auth, Dashboard, Transactions, Tax Calculation, Export (CSV/PDF), Team, Notifications
"""

import pytest
import requests
import os
import json
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tax-naira.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@nairatrack.ng"
ADMIN_PASSWORD = "NairaTrack2024!"


@pytest.fixture(scope="module")
def api_session():
    """Create a session for API requests"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def admin_session(api_session):
    """Login as admin and return authenticated session"""
    response = api_session.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return api_session


@pytest.fixture(scope="module")
def test_user_session():
    """Create and login a test user"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    timestamp = datetime.now().strftime("%H%M%S%f")
    test_email = f"testuser_{timestamp}@example.com"
    
    # Register
    response = session.post(f"{BASE_URL}/api/auth/register", json={
        "email": test_email,
        "password": "TestPass123!",
        "name": f"Test User {timestamp}",
        "business_type": "freelancer",
        "monthly_income_range": "100000-500000"
    })
    assert response.status_code == 200, f"Registration failed: {response.text}"
    
    return session, test_email


# ========================
# HEALTH CHECK TESTS
# ========================

class TestHealthCheck:
    """Health check endpoint tests"""
    
    def test_api_root(self, api_session):
        """Test API root endpoint"""
        response = api_session.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "NairaTrack" in data["message"]
        print(f"✅ API Root: {data['message']}")
    
    def test_health_endpoint(self, api_session):
        """Test health endpoint"""
        response = api_session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✅ Health: {data['status']}")


# ========================
# AUTH TESTS
# ========================

class TestAuth:
    """Authentication endpoint tests"""
    
    def test_admin_login(self, api_session):
        """Test admin login with correct credentials"""
        response = api_session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["email"] == ADMIN_EMAIL
        assert data["subscription_plan"] == "business"
        print(f"✅ Admin login successful: {data['name']}")
    
    def test_login_invalid_credentials(self, api_session):
        """Test login with invalid credentials"""
        response = api_session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        print("✅ Invalid login rejected correctly")
    
    def test_user_registration(self, api_session):
        """Test user registration"""
        timestamp = datetime.now().strftime("%H%M%S%f")
        response = api_session.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"newuser_{timestamp}@example.com",
            "password": "NewPass123!",
            "name": f"New User {timestamp}",
            "business_type": "sme",
            "monthly_income_range": "500000-1000000"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["subscription_plan"] == "starter"
        print(f"✅ User registration successful: {data['id']}")
    
    def test_get_me(self, admin_session):
        """Test get current user profile"""
        response = admin_session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "business_type" in data
        print(f"✅ Get me: {data['name']} ({data['business_type']})")


# ========================
# DASHBOARD TESTS
# ========================

class TestDashboard:
    """Dashboard endpoint tests"""
    
    def test_dashboard_data(self, admin_session):
        """Test dashboard returns all required fields"""
        response = admin_session.get(f"{BASE_URL}/api/dashboard")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields
        required_fields = [
            "total_income", "total_expenses", "net_income", 
            "total_bank_balance", "estimated_tax", "tax_health_score",
            "spending_breakdown", "business_type", "subscription_plan"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        assert isinstance(data["tax_health_score"], int)
        assert 0 <= data["tax_health_score"] <= 100
        print(f"✅ Dashboard: Tax Health Score = {data['tax_health_score']}, Income = ₦{data['total_income']:,.0f}")


# ========================
# TRANSACTION TESTS
# ========================

class TestTransactions:
    """Transaction CRUD tests"""
    
    def test_create_transaction(self, admin_session):
        """Test creating a transaction"""
        response = admin_session.post(f"{BASE_URL}/api/transactions", json={
            "amount": 75000,
            "type": "income",
            "category": "Sales",
            "description": "TEST_Transaction for testing"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["amount"] == 75000
        assert data["type"] == "income"
        print(f"✅ Transaction created: {data['id']}")
        return data["id"]
    
    def test_get_transactions(self, admin_session):
        """Test getting transactions list"""
        response = admin_session.get(f"{BASE_URL}/api/transactions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Transactions retrieved: {len(data)} items")
    
    def test_delete_transaction(self, admin_session):
        """Test deleting a transaction"""
        # First create a transaction
        create_response = admin_session.post(f"{BASE_URL}/api/transactions", json={
            "amount": 1000,
            "type": "expense",
            "category": "Miscellaneous",
            "description": "TEST_To be deleted"
        })
        assert create_response.status_code == 200
        tx_id = create_response.json()["id"]
        
        # Delete it
        delete_response = admin_session.delete(f"{BASE_URL}/api/transactions/{tx_id}")
        assert delete_response.status_code == 200
        print(f"✅ Transaction deleted: {tx_id}")


# ========================
# TAX CALCULATION TESTS
# ========================

class TestTaxCalculation:
    """Tax calculation endpoint tests"""
    
    def test_tax_calculation(self, admin_session):
        """Test tax calculation returns proper breakdown"""
        response = admin_session.get(f"{BASE_URL}/api/tax-calculation")
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            "gross_income", "total_expenses", "deductible_expenses",
            "taxable_income", "income_tax", "tax_type", "vat", "total_tax_owed"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify tax type based on business type
        assert data["tax_type"] in ["Personal Income Tax (PITA)", "Company Income Tax (CITA)"]
        print(f"✅ Tax Calculation: {data['tax_type']}, Tax = ₦{data['income_tax']:,.0f}")


# ========================
# EXPORT TESTS (NEW FEATURES)
# ========================

class TestExport:
    """Export functionality tests - CSV and PDF"""
    
    def test_export_transactions_csv(self, admin_session):
        """Test exporting transactions as CSV"""
        response = admin_session.get(f"{BASE_URL}/api/export/transactions?format=csv&period=all")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("Content-Type", "")
        assert "attachment" in response.headers.get("Content-Disposition", "")
        print(f"✅ Transaction CSV export: {len(response.content)} bytes")
    
    def test_export_transactions_json(self, admin_session):
        """Test exporting transactions as JSON"""
        response = admin_session.get(f"{BASE_URL}/api/export/transactions?format=json&period=all")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("Content-Type", "")
        print(f"✅ Transaction JSON export: {len(response.content)} bytes")
    
    def test_export_tax_report_pdf(self, admin_session):
        """Test exporting tax report as PDF"""
        response = admin_session.get(f"{BASE_URL}/api/export/tax-report?format=pdf")
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("Content-Type", "")
        assert "attachment" in response.headers.get("Content-Disposition", "")
        # Verify it's a valid PDF (starts with %PDF)
        assert response.content[:4] == b'%PDF', "Invalid PDF format"
        print(f"✅ Tax Report PDF export: {len(response.content)} bytes")
    
    def test_export_tax_report_csv(self, admin_session):
        """Test exporting tax report as CSV"""
        response = admin_session.get(f"{BASE_URL}/api/export/tax-report?format=csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("Content-Type", "")
        print(f"✅ Tax Report CSV export: {len(response.content)} bytes")
    
    def test_export_tax_report_json(self, admin_session):
        """Test exporting tax report as JSON"""
        response = admin_session.get(f"{BASE_URL}/api/export/tax-report?format=json")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert "summary" in data
        assert "tax_year" in data
        print(f"✅ Tax Report JSON export: Year {data['tax_year']}")
    
    def test_export_requires_subscription(self, test_user_session):
        """Test that export requires Growth+ plan"""
        session, _ = test_user_session
        response = session.get(f"{BASE_URL}/api/export/transactions?format=csv")
        assert response.status_code == 403
        print("✅ Export correctly requires Growth+ plan")


# ========================
# TEAM ACCESS TESTS (NEW FEATURES)
# ========================

class TestTeamAccess:
    """Team member management tests - Business plan feature"""
    
    def test_invite_team_member(self, admin_session):
        """Test inviting a team member"""
        timestamp = datetime.now().strftime("%H%M%S%f")
        response = admin_session.post(f"{BASE_URL}/api/team/invite", json={
            "email": f"team_{timestamp}@example.com",
            "role": "viewer"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"
        assert data["role"] == "viewer"
        print(f"✅ Team member invited: {data['email']}")
    
    def test_get_team_members(self, admin_session):
        """Test getting team members list"""
        response = admin_session.get(f"{BASE_URL}/api/team/members")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Team members retrieved: {len(data)} members")
    
    def test_team_requires_business_plan(self, test_user_session):
        """Test that team features require Business plan"""
        session, _ = test_user_session
        response = session.post(f"{BASE_URL}/api/team/invite", json={
            "email": "test@example.com",
            "role": "viewer"
        })
        assert response.status_code == 403
        print("✅ Team invite correctly requires Business plan")
    
    def test_duplicate_invite_rejected(self, admin_session):
        """Test that duplicate invites are rejected"""
        timestamp = datetime.now().strftime("%H%M%S%f")
        email = f"duplicate_{timestamp}@example.com"
        
        # First invite
        response1 = admin_session.post(f"{BASE_URL}/api/team/invite", json={
            "email": email,
            "role": "viewer"
        })
        assert response1.status_code == 200
        
        # Duplicate invite
        response2 = admin_session.post(f"{BASE_URL}/api/team/invite", json={
            "email": email,
            "role": "accountant"
        })
        assert response2.status_code == 400
        print("✅ Duplicate team invite correctly rejected")


# ========================
# NOTIFICATIONS TESTS (NEW FEATURES)
# ========================

class TestNotifications:
    """Notification system tests"""
    
    def test_get_notifications(self, admin_session):
        """Test getting notifications list"""
        response = admin_session.get(f"{BASE_URL}/api/notifications")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Notifications retrieved: {len(data)} items")
    
    def test_get_unread_count(self, admin_session):
        """Test getting unread notification count"""
        response = admin_session.get(f"{BASE_URL}/api/notifications/unread-count")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert isinstance(data["count"], int)
        print(f"✅ Unread notifications: {data['count']}")
    
    def test_mark_notifications_read(self, admin_session):
        """Test marking notifications as read"""
        response = admin_session.post(f"{BASE_URL}/api/notifications/mark-read", json={
            "ids": []  # Mark all as read
        })
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print("✅ Notifications marked as read")
    
    def test_check_deadline_notifications(self, admin_session):
        """Test deadline notification check"""
        response = admin_session.post(f"{BASE_URL}/api/notifications/check-deadlines")
        assert response.status_code == 200
        data = response.json()
        assert "notifications_created" in data
        print(f"✅ Deadline check: {data['notifications_created']} notifications created")


# ========================
# BANK & SUBSCRIPTION TESTS
# ========================

class TestBankAndSubscription:
    """Bank accounts and subscription tests"""
    
    def test_get_supported_banks(self, api_session):
        """Test getting supported Nigerian banks"""
        response = api_session.get(f"{BASE_URL}/api/banks")
        assert response.status_code == 200
        data = response.json()
        assert "banks" in data
        assert len(data["banks"]) >= 5
        assert "GTBank" in data["banks"]
        print(f"✅ Supported banks: {len(data['banks'])} banks")
    
    def test_get_subscription_plans(self, api_session):
        """Test getting subscription plans"""
        response = api_session.get(f"{BASE_URL}/api/subscription/plans")
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        assert len(data["plans"]) == 3
        
        # Verify plan prices
        plans = {p["id"]: p for p in data["plans"]}
        assert plans["starter"]["price"] == 2000
        assert plans["growth"]["price"] == 4000
        assert plans["business"]["price"] == 6000
        print("✅ Subscription plans: Starter ₦2k, Growth ₦4k, Business ₦6k")
    
    def test_link_bank_account(self, admin_session):
        """Test linking a bank account (mock)"""
        response = admin_session.post(f"{BASE_URL}/api/bank-accounts", json={
            "bank_name": "Access Bank",
            "account_number": "0987654321",
            "account_name": "Test Business Account"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["linked"] == True
        print(f"✅ Bank account linked: {data['bank_name']}")
    
    def test_get_bank_accounts(self, admin_session):
        """Test getting linked bank accounts"""
        response = admin_session.get(f"{BASE_URL}/api/bank-accounts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Bank accounts: {len(data)} linked")


# ========================
# AI CHAT TESTS
# ========================

class TestAIChat:
    """AI Chat Assistant tests"""
    
    def test_chat_message(self, admin_session):
        """Test sending a chat message"""
        response = admin_session.post(f"{BASE_URL}/api/chat", json={
            "message": "What is the VAT rate in Nigeria?",
            "session_id": f"test-{datetime.now().strftime('%H%M%S')}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "session_id" in data
        assert len(data["response"]) > 0
        print(f"✅ AI Chat response received: {len(data['response'])} chars")
    
    def test_chat_history(self, admin_session):
        """Test getting chat history"""
        response = admin_session.get(f"{BASE_URL}/api/chat/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Chat history: {len(data)} messages")


# ========================
# TAX FILING GUIDE TESTS
# ========================

class TestTaxFilingGuide:
    """Tax filing guide and checklist tests"""
    
    def test_filing_guide(self, admin_session):
        """Test getting tax filing guide"""
        response = admin_session.get(f"{BASE_URL}/api/tax-filing/guide")
        assert response.status_code == 200
        data = response.json()
        assert "steps" in data
        assert "documents_needed" in data
        assert "deadlines" in data
        assert len(data["steps"]) >= 5
        print(f"✅ Filing guide: {len(data['steps'])} steps")
    
    def test_filing_checklist(self, admin_session):
        """Test getting filing checklist"""
        response = admin_session.get(f"{BASE_URL}/api/tax-filing/checklist")
        assert response.status_code == 200
        data = response.json()
        assert "checklist" in data
        assert "progress_percentage" in data
        assert 0 <= data["progress_percentage"] <= 100
        print(f"✅ Filing checklist: {data['progress_percentage']}% complete")


# ========================
# EDUCATION TESTS
# ========================

class TestEducation:
    """Education articles tests"""
    
    def test_get_articles(self, api_session):
        """Test getting education articles"""
        response = api_session.get(f"{BASE_URL}/api/education/articles")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 4
        print(f"✅ Education articles: {len(data)} articles")
    
    def test_get_article_by_id(self, api_session):
        """Test getting a specific article"""
        response = api_session.get(f"{BASE_URL}/api/education/articles/1")
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "content" in data
        print(f"✅ Article retrieved: {data['title']}")


# ========================
# CATEGORIES TESTS
# ========================

class TestCategories:
    """Transaction categories tests"""
    
    def test_get_categories(self, api_session):
        """Test getting transaction categories"""
        response = api_session.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 200
        data = response.json()
        assert "income" in data
        assert "expense" in data
        assert len(data["income"]) >= 5
        assert len(data["expense"]) >= 5
        print(f"✅ Categories: {len(data['income'])} income, {len(data['expense'])} expense")


# ========================
# RECEIPTS TESTS
# ========================

class TestReceipts:
    """Receipt management tests"""
    
    def test_get_receipts(self, admin_session):
        """Test getting receipts list"""
        response = admin_session.get(f"{BASE_URL}/api/receipts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Receipts: {len(data)} items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
