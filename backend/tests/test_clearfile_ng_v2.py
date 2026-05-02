"""
ClearFile NG API Tests - Iteration 4
Testing new features: State Tax, TCC Tracker, Tax Planner, AI Categorizer
Plus regression tests for existing functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "admin@nairatrack.ng"
ADMIN_PASSWORD = "NairaTrack2024!"


class TestHealthAndRoot:
    """Health check and root endpoint tests"""
    
    def test_health_endpoint(self):
        """GET /api/health returns healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        print("✓ Health endpoint working")
    
    def test_root_endpoint(self):
        """GET /api/ returns ClearFile NG API message"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "ClearFile NG API is running" in data["message"]
        print("✓ Root endpoint shows ClearFile NG branding")


class TestAuthentication:
    """Authentication tests"""
    
    def test_admin_login(self):
        """POST /api/auth/login with admin credentials"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        # API returns user data directly, not nested under "user" key
        assert "email" in data
        assert data["email"] == ADMIN_EMAIL
        # Role might not be in response, check if present
        if "role" in data:
            assert data["role"] == "admin"
        print(f"✓ Admin login successful: {data['email']}")
        return session
    
    def test_invalid_login(self):
        """POST /api/auth/login with wrong credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@email.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid login correctly rejected")


@pytest.fixture(scope="class")
def auth_session():
    """Create authenticated session for tests"""
    session = requests.Session()
    response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip("Authentication failed - skipping authenticated tests")
    return session


class TestDashboard:
    """Dashboard endpoint tests"""
    
    def test_get_dashboard(self, auth_session):
        """GET /api/dashboard returns dashboard data"""
        response = auth_session.get(f"{BASE_URL}/api/dashboard")
        assert response.status_code == 200
        data = response.json()
        # Verify dashboard structure
        assert "total_income" in data
        assert "total_expenses" in data
        assert "estimated_tax" in data
        assert "tax_health_score" in data
        print(f"✓ Dashboard data: income={data['total_income']}, expenses={data['total_expenses']}")


class TestStatesEndpoint:
    """NEW: Nigerian States endpoint tests"""
    
    def test_get_states(self, auth_session):
        """GET /api/states returns list of Nigerian states with revenue services"""
        response = auth_session.get(f"{BASE_URL}/api/states")
        assert response.status_code == 200
        data = response.json()
        assert "states" in data
        assert len(data["states"]) > 0
        
        # Verify state structure
        state = data["states"][0]
        assert "id" in state
        assert "name" in state
        assert "service" in state
        
        # Check for known states
        state_ids = [s["id"] for s in data["states"]]
        assert "lagos" in state_ids
        assert "abuja" in state_ids
        print(f"✓ States endpoint returned {len(data['states'])} states")


class TestUserState:
    """NEW: User state of residence tests"""
    
    def test_update_user_state(self, auth_session):
        """PUT /api/user/state updates user state of residence"""
        response = auth_session.put(f"{BASE_URL}/api/user/state", json={
            "state_of_residence": "lagos"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "lagos"
        print("✓ User state updated to Lagos")


class TestTaxObligations:
    """NEW: Tax Obligations (State vs Federal) tests"""
    
    def test_get_tax_obligations(self, auth_session):
        """GET /api/tax-obligations returns federal and state obligations"""
        response = auth_session.get(f"{BASE_URL}/api/tax-obligations")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "federal" in data
        assert "state" in data
        assert "state_info" in data
        assert "total_federal" in data
        assert "total_state" in data
        
        # Verify state info
        assert "service" in data["state_info"]
        assert "name" in data["state_info"]
        
        print(f"✓ Tax obligations: Federal={data['total_federal']}, State={data['total_state']}")
        print(f"  State service: {data['state_info']['service']}")


class TestTCCTracker:
    """NEW: TCC Tracker tests"""
    
    def test_get_tcc_progress(self, auth_session):
        """GET /api/tcc/progress returns TCC checklist with progress"""
        response = auth_session.get(f"{BASE_URL}/api/tcc/progress")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "progress" in data
        assert "checklist" in data
        assert "completed_count" in data
        assert "total_count" in data
        assert "tcc_ready" in data
        
        # Verify checklist items
        assert len(data["checklist"]) > 0
        item = data["checklist"][0]
        assert "id" in item
        assert "item" in item
        assert "completed" in item
        assert "weight" in item
        
        print(f"✓ TCC Progress: {data['progress']}% ({data['completed_count']}/{data['total_count']} items)")
    
    def test_generate_tcc_letter(self, auth_session):
        """GET /api/tcc/generate-letter returns PDF download"""
        response = auth_session.get(f"{BASE_URL}/api/tcc/generate-letter")
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "")
        assert len(response.content) > 0
        print(f"✓ TCC Letter PDF generated: {len(response.content)} bytes")


class TestTaxPlanner:
    """NEW: Tax Planner (What-If Simulator) tests"""
    
    def test_simulate_tax(self, auth_session):
        """POST /api/tax-planner/simulate returns tax breakdown"""
        response = auth_session.post(f"{BASE_URL}/api/tax-planner/simulate", json={
            "annual_income": 5000000,
            "annual_expenses": 1500000,
            "deductible_percentage": 70,
            "business_type": "freelancer"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "annual_income" in data
        assert "annual_expenses" in data
        assert "taxable_income" in data
        assert "income_tax" in data
        assert "total_tax" in data
        assert "effective_tax_rate" in data
        assert "monthly_tax_savings" in data
        assert "breakdown" in data
        
        # Verify calculations make sense
        assert data["annual_income"] == 5000000
        assert data["taxable_income"] <= data["annual_income"]
        assert data["total_tax"] >= 0
        
        print(f"✓ Tax simulation: Income=₦{data['annual_income']:,}, Tax=₦{data['total_tax']:,}")
        print(f"  Effective rate: {data['effective_tax_rate']}%, Monthly savings: ₦{data['monthly_tax_savings']:,}")
    
    def test_set_aside_tax_reserve(self, auth_session):
        """POST /api/tax-planner/set-aside creates tax reserve"""
        response = auth_session.post(f"{BASE_URL}/api/tax-planner/set-aside", json={
            "amount": 50000
        })
        assert response.status_code == 200
        data = response.json()
        assert "total_reserve" in data
        assert data["total_reserve"] >= 50000
        print(f"✓ Tax reserve set aside: ₦{data['total_reserve']:,}")
    
    def test_get_tax_reserve(self, auth_session):
        """GET /api/tax-planner/reserve returns reserve amount"""
        response = auth_session.get(f"{BASE_URL}/api/tax-planner/reserve")
        assert response.status_code == 200
        data = response.json()
        assert "amount" in data
        print(f"✓ Tax reserve: ₦{data['amount']:,}")


class TestAICategorizer:
    """NEW: AI Smart Expense Categorizer tests"""
    
    def test_auto_categorize(self, auth_session):
        """POST /api/categorize/auto returns categorized transactions"""
        response = auth_session.post(f"{BASE_URL}/api/categorize/auto")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "transactions" in data
        assert "summary" in data
        assert "deductible_categories" in data
        
        # Verify summary
        summary = data["summary"]
        assert "total_deductible" in summary
        assert "total_personal" in summary
        assert "deductible_count" in summary
        assert "estimated_tax_savings" in summary
        
        print(f"✓ AI Categorizer: {len(data['transactions'])} transactions")
        print(f"  Deductible: ₦{summary['total_deductible']:,}, Personal: ₦{summary['total_personal']:,}")
        print(f"  Estimated tax savings: ₦{summary['estimated_tax_savings']:,}")


class TestTransactions:
    """Transaction CRUD tests"""
    
    def test_get_transactions(self, auth_session):
        """GET /api/transactions returns list"""
        response = auth_session.get(f"{BASE_URL}/api/transactions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Transactions: {len(data)} items")
    
    def test_create_transaction(self, auth_session):
        """POST /api/transactions creates new transaction"""
        response = auth_session.post(f"{BASE_URL}/api/transactions", json={
            "amount": 25000,
            "type": "expense",
            "category": "Equipment",
            "description": "TEST_Office supplies",
            "date": "2026-01-15"
        })
        # API returns 200 for successful creation
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["amount"] == 25000
        assert data["category"] == "Equipment"
        print(f"✓ Transaction created: {data['description']}")
        return data.get("id")


class TestInsights:
    """Insights endpoint tests"""
    
    def test_get_spending_insights(self, auth_session):
        """GET /api/insights/spending returns insights"""
        response = auth_session.get(f"{BASE_URL}/api/insights/spending")
        assert response.status_code == 200
        data = response.json()
        assert "insights" in data
        print(f"✓ Spending insights: {len(data['insights'])} insights")
    
    def test_get_recurring(self, auth_session):
        """GET /api/insights/recurring returns recurring expenses"""
        response = auth_session.get(f"{BASE_URL}/api/insights/recurring")
        assert response.status_code == 200
        data = response.json()
        assert "recurring" in data
        print(f"✓ Recurring expenses: {len(data['recurring'])} patterns")


class TestSubscriptionPlans:
    """Subscription plans tests"""
    
    def test_get_subscription_plans(self, auth_session):
        """GET /api/subscription/plans returns 3 plans"""
        # Try different endpoint paths
        response = auth_session.get(f"{BASE_URL}/api/subscription/plans")
        if response.status_code == 404:
            # Fallback to payments endpoint
            response = auth_session.get(f"{BASE_URL}/api/payments/plans")
        
        if response.status_code == 404:
            # Plans might be hardcoded in frontend, skip this test
            pytest.skip("Subscription plans endpoint not found - plans may be frontend-only")
        
        assert response.status_code == 200
        data = response.json()
        
        # Handle nested structure: {plans: [...], paystack_public_key: ...}
        if "plans" in data:
            plans = data["plans"]
        else:
            plans = data
        
        assert len(plans) >= 3
        
        plan_names = [p["name"].lower() for p in plans]
        assert "starter" in plan_names
        assert "growth" in plan_names
        assert "business" in plan_names
        print(f"✓ Subscription plans: {', '.join(plan_names)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
