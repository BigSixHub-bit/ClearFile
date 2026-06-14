"""
ClearFile NG Dark Theme Regression Tests
Tests all API endpoints after visual redesign to ensure backend functionality is intact.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "admin@clearfileng.com"
ADMIN_PASSWORD = "ClearFileNG2024!"


class TestHealthAndBasics:
    """Health check and basic API tests"""
    
    def test_health_endpoint(self):
        """GET /api/health returns healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health check passed: {data}")
    
    def test_root_endpoint(self):
        """GET /api/ returns API info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "ClearFile NG" in data.get("message", "")
        print(f"✓ Root endpoint passed: {data}")


class TestAuthentication:
    """Authentication flow tests"""
    
    @pytest.fixture
    def session(self):
        return requests.Session()
    
    def test_admin_login(self, session):
        """POST /api/auth/login with admin credentials"""
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # Login returns user data directly (not wrapped in "user" key)
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "admin"
        print(f"✓ Admin login passed: role={data['role']}")
        return session
    
    def test_get_current_user(self, session):
        """GET /api/auth/me returns user info"""
        # First login
        session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        response = session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        print(f"✓ Get current user passed: {data['email']}")


class TestDashboard:
    """Dashboard API tests"""
    
    @pytest.fixture
    def auth_session(self):
        session = requests.Session()
        session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return session
    
    def test_get_dashboard(self, auth_session):
        """GET /api/dashboard returns dashboard data"""
        response = auth_session.get(f"{BASE_URL}/api/dashboard")
        assert response.status_code == 200
        data = response.json()
        # Verify dashboard structure
        assert "total_income" in data
        assert "total_expenses" in data
        assert "estimated_tax" in data
        assert "total_bank_balance" in data
        assert "tax_health_score" in data
        assert "spending_breakdown" in data
        print(f"✓ Dashboard passed: income={data['total_income']}, expenses={data['total_expenses']}")


class TestTransactions:
    """Transaction CRUD tests"""
    
    @pytest.fixture
    def auth_session(self):
        session = requests.Session()
        session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return session
    
    def test_get_transactions(self, auth_session):
        """GET /api/transactions returns list"""
        response = auth_session.get(f"{BASE_URL}/api/transactions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Get transactions passed: {len(data)} transactions")
    
    def test_create_transaction(self, auth_session):
        """POST /api/transactions creates transaction"""
        tx_data = {
            "amount": 50000,
            "type": "income",
            "category": "Sales",
            "description": "TEST_regression_test_transaction"
        }
        response = auth_session.post(f"{BASE_URL}/api/transactions", json=tx_data)
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 50000
        assert data["type"] == "income"
        assert "id" in data
        print(f"✓ Create transaction passed: id={data['id']}")
        
        # Cleanup - delete the test transaction
        auth_session.delete(f"{BASE_URL}/api/transactions/{data['id']}")


class TestTaxCalculation:
    """Tax calculation tests"""
    
    @pytest.fixture
    def auth_session(self):
        session = requests.Session()
        session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return session
    
    def test_get_tax_calculation(self, auth_session):
        """GET /api/tax-calculation returns tax breakdown"""
        response = auth_session.get(f"{BASE_URL}/api/tax-calculation")
        assert response.status_code == 200
        data = response.json()
        assert "gross_income" in data
        assert "taxable_income" in data
        assert "income_tax" in data
        assert "total_tax_owed" in data
        assert "tax_type" in data
        print(f"✓ Tax calculation passed: tax_owed={data['total_tax_owed']}, type={data['tax_type']}")


class TestInsights:
    """Insights API tests"""
    
    @pytest.fixture
    def auth_session(self):
        session = requests.Session()
        session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return session
    
    def test_get_spending_insights(self, auth_session):
        """GET /api/insights/spending returns insights"""
        response = auth_session.get(f"{BASE_URL}/api/insights/spending")
        assert response.status_code == 200
        data = response.json()
        assert "insights" in data
        assert "summary" in data
        print(f"✓ Spending insights passed: {len(data['insights'])} insights")
    
    def test_get_recurring_insights(self, auth_session):
        """GET /api/insights/recurring returns recurring data"""
        response = auth_session.get(f"{BASE_URL}/api/insights/recurring")
        assert response.status_code == 200
        data = response.json()
        assert "recurring" in data
        assert "total_monthly_recurring" in data
        print(f"✓ Recurring insights passed: {len(data['recurring'])} recurring items")


class TestTCCProgress:
    """TCC Tracker tests"""
    
    @pytest.fixture
    def auth_session(self):
        session = requests.Session()
        session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return session
    
    def test_get_tcc_progress(self, auth_session):
        """GET /api/tcc/progress returns TCC progress"""
        response = auth_session.get(f"{BASE_URL}/api/tcc/progress")
        assert response.status_code == 200
        data = response.json()
        assert "progress" in data
        assert "checklist" in data
        assert "tcc_ready" in data
        print(f"✓ TCC progress passed: {data['progress']}% complete")


class TestAdminStats:
    """Admin panel tests"""
    
    @pytest.fixture
    def auth_session(self):
        session = requests.Session()
        session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return session
    
    def test_get_admin_stats(self, auth_session):
        """GET /api/admin/stats returns admin stats"""
        response = auth_session.get(f"{BASE_URL}/api/admin/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_transactions" in data
        assert "expert_requests" in data
        print(f"✓ Admin stats passed: {data['total_users']} users, {data['total_transactions']} transactions")


class TestTaxGuide:
    """Tax guide and education tests"""
    
    @pytest.fixture
    def auth_session(self):
        session = requests.Session()
        session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return session
    
    def test_get_filing_guide(self, auth_session):
        """GET /api/tax-filing/guide returns guide"""
        response = auth_session.get(f"{BASE_URL}/api/tax-filing/guide")
        assert response.status_code == 200
        data = response.json()
        assert "steps" in data
        assert "documents_needed" in data
        print(f"✓ Filing guide passed: {len(data['steps'])} steps")
    
    def test_get_education_articles(self, auth_session):
        """GET /api/education/articles returns articles"""
        response = auth_session.get(f"{BASE_URL}/api/education/articles")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Education articles passed: {len(data)} articles")


class TestTaxObligations:
    """Tax obligations routing tests"""
    
    @pytest.fixture
    def auth_session(self):
        session = requests.Session()
        session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return session
    
    def test_get_tax_obligations(self, auth_session):
        """GET /api/tax-obligations returns federal/state breakdown"""
        response = auth_session.get(f"{BASE_URL}/api/tax-obligations")
        assert response.status_code == 200
        data = response.json()
        assert "federal" in data
        assert "state" in data
        assert "state_info" in data
        print(f"✓ Tax obligations passed: {len(data['federal'])} federal, {len(data['state'])} state")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
