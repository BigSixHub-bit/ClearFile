"""
ClearFile NG API Tests - Iteration 5
Testing NEW features: AI Tax Guide (6-step walkthrough) + Expert Matching Form
Plus regression tests for existing functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "admin@clearfileng.com"
ADMIN_PASSWORD = "ClearFileNG2024!"


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
        assert "email" in data
        assert data["email"] == ADMIN_EMAIL
        print(f"✓ Admin login successful: {data['email']}")
        return session


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


# ========================
# NEW: AI TAX GUIDE TESTS
# ========================

class TestAITaxGuideWalkthrough:
    """NEW: AI Tax Guide - 6-step FIRS filing walkthrough tests"""
    
    def test_ai_walkthrough_step1(self, auth_session):
        """POST /api/tax-guide/ai-walkthrough with step 1 returns title, instructions, portal, tip, user_summary"""
        response = auth_session.post(f"{BASE_URL}/api/tax-guide/ai-walkthrough", json={
            "step": 1
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "step" in data
        assert data["step"] == 1
        assert "total_steps" in data
        assert data["total_steps"] == 6
        assert "title" in data
        assert "instructions" in data
        assert "portal" in data
        assert "tip" in data
        assert "user_summary" in data
        assert "session_id" in data
        
        # Verify user_summary structure
        user_summary = data["user_summary"]
        assert "business_type" in user_summary
        assert "state" in user_summary
        assert "gross_income" in user_summary
        assert "total_tax" in user_summary
        assert "tax_type" in user_summary
        
        # Step 1 should have portal link
        assert data["portal"] is not None
        assert "taxpromax" in data["portal"].lower()
        
        print(f"✓ AI Walkthrough Step 1: {data['title']}")
        print(f"  Portal: {data['portal']}")
        print(f"  User Summary: Income={user_summary['gross_income']}, Tax={user_summary['total_tax']}, Type={user_summary['tax_type']}")
        
        return data["session_id"]
    
    def test_ai_walkthrough_step3_income_data(self, auth_session):
        """POST /api/tax-guide/ai-walkthrough with step 3 returns income data in your_data field"""
        response = auth_session.post(f"{BASE_URL}/api/tax-guide/ai-walkthrough", json={
            "step": 3
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data["step"] == 3
        assert "your_data" in data
        assert data["your_data"] is not None
        
        # Step 3 should have gross_income in your_data
        your_data = data["your_data"]
        assert "gross_income" in your_data
        
        print(f"✓ AI Walkthrough Step 3: {data['title']}")
        print(f"  Your Data: gross_income={your_data['gross_income']}")
    
    def test_ai_walkthrough_step6_final_submit(self, auth_session):
        """POST /api/tax-guide/ai-walkthrough with step 6 returns final submit instructions with total_to_pay"""
        response = auth_session.post(f"{BASE_URL}/api/tax-guide/ai-walkthrough", json={
            "step": 6
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data["step"] == 6
        assert "your_data" in data
        assert data["your_data"] is not None
        
        # Step 6 should have total_to_pay
        your_data = data["your_data"]
        assert "total_to_pay" in your_data
        
        # Step 6 should have portal link for final submission
        assert data["portal"] is not None
        
        print(f"✓ AI Walkthrough Step 6: {data['title']}")
        print(f"  Total to Pay: {your_data['total_to_pay']}")
        print(f"  Portal: {data['portal']}")
    
    def test_ai_walkthrough_all_steps(self, auth_session):
        """Test all 6 steps of the AI walkthrough"""
        session_id = None
        
        for step in range(1, 7):
            payload = {"step": step}
            if session_id:
                payload["session_id"] = session_id
            
            response = auth_session.post(f"{BASE_URL}/api/tax-guide/ai-walkthrough", json=payload)
            assert response.status_code == 200, f"Step {step} failed with status {response.status_code}"
            data = response.json()
            
            assert data["step"] == step
            assert data["total_steps"] == 6
            assert "title" in data
            assert "instructions" in data
            assert isinstance(data["instructions"], list)
            assert len(data["instructions"]) > 0
            
            if not session_id:
                session_id = data["session_id"]
            
            print(f"  Step {step}: {data['title']}")
        
        print(f"✓ All 6 AI Walkthrough steps working")


# ========================
# NEW: EXPERT MATCHING TESTS
# ========================

class TestExpertMatching:
    """NEW: Expert Matching Form tests"""
    
    def test_request_expert(self, auth_session):
        """POST /api/experts/request with phone, service_type, urgency creates expert request"""
        response = auth_session.post(f"{BASE_URL}/api/experts/request", json={
            "phone": "08012345678",
            "email": "test@example.com",
            "service_type": "full_filing",
            "urgency": "normal",
            "budget_range": "10k_25k",
            "notes": "TEST_Need help with annual filing"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "message" in data
        assert "request_id" in data
        assert "estimated_match_time" in data
        
        # Verify values
        assert "success" in data["message"].lower()
        assert data["request_id"] is not None
        assert "24-48" in data["estimated_match_time"]
        
        print(f"✓ Expert request created: {data['request_id']}")
        print(f"  Estimated match time: {data['estimated_match_time']}")
        
        return data["request_id"]
    
    def test_get_expert_requests(self, auth_session):
        """GET /api/experts/requests returns list of user's expert requests"""
        response = auth_session.get(f"{BASE_URL}/api/experts/requests")
        assert response.status_code == 200
        data = response.json()
        
        assert "requests" in data
        assert isinstance(data["requests"], list)
        
        # Should have at least one request from previous test
        if len(data["requests"]) > 0:
            request = data["requests"][0]
            assert "id" in request
            assert "service_type" in request
            assert "urgency" in request
            assert "status" in request
            print(f"✓ Expert requests: {len(data['requests'])} requests found")
            print(f"  Latest: service_type={request['service_type']}, status={request['status']}")
        else:
            print("✓ Expert requests endpoint working (no requests yet)")


# ========================
# REGRESSION TESTS
# ========================

class TestRegressionTaxCalculation:
    """Regression: Tax Calculation endpoint"""
    
    def test_get_tax_calculation(self, auth_session):
        """GET /api/tax-calculation still returns tax breakdown"""
        response = auth_session.get(f"{BASE_URL}/api/tax-calculation")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "gross_income" in data
        assert "deductible_expenses" in data
        assert "taxable_income" in data
        assert "income_tax" in data
        assert "total_tax_owed" in data
        assert "tax_type" in data
        assert "business_type" in data
        
        print(f"✓ Tax Calculation: Income={data['gross_income']}, Tax={data['total_tax_owed']}, Type={data['tax_type']}")


class TestRegressionDashboard:
    """Regression: Dashboard endpoint"""
    
    def test_get_dashboard(self, auth_session):
        """GET /api/dashboard still returns dashboard data"""
        response = auth_session.get(f"{BASE_URL}/api/dashboard")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "total_income" in data
        assert "total_expenses" in data
        assert "estimated_tax" in data
        assert "tax_health_score" in data
        
        print(f"✓ Dashboard: Income={data['total_income']}, Expenses={data['total_expenses']}, Tax={data['estimated_tax']}")


class TestRegressionTransactions:
    """Regression: Transactions endpoint"""
    
    def test_get_transactions(self, auth_session):
        """GET /api/transactions returns list"""
        response = auth_session.get(f"{BASE_URL}/api/transactions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Transactions: {len(data)} items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
