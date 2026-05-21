"""
Admin Panel API Tests - Iteration 6
Tests for admin dashboard stats, expert request management, user management
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "admin@clearfileng.com"
ADMIN_PASSWORD = "ClearFileNG2024!"

# Test user credentials (non-admin)
TEST_USER_EMAIL = f"testuser_{uuid.uuid4().hex[:8]}@test.com"
TEST_USER_PASSWORD = "TestPass123!"
TEST_USER_NAME = "Test User"


class TestHealthCheck:
    """Basic health check"""
    
    def test_health_endpoint(self):
        """GET /api/health returns healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health check passed")


class TestAdminAuthentication:
    """Admin login and role verification"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Login as admin and return session with cookies"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert data.get("role") == "admin", f"Expected role=admin, got {data.get('role')}"
        print(f"✓ Admin login successful, role={data.get('role')}")
        return session
    
    def test_admin_login_returns_role(self, admin_session):
        """POST /api/auth/login returns role field for admin user"""
        # Already verified in fixture, just confirm session works
        response = admin_session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "role" in data, "Role field missing from /auth/me response"
        assert data["role"] == "admin", f"Expected admin role, got {data['role']}"
        print(f"✓ GET /api/auth/me returns role=admin")
    
    def test_auth_me_returns_role_field(self, admin_session):
        """GET /api/auth/me returns role field"""
        response = admin_session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        required_fields = ["id", "email", "name", "role", "subscription_plan"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        print(f"✓ /api/auth/me returns all required fields including role")


class TestAdminStats:
    """Admin dashboard statistics"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return session
    
    def test_get_admin_stats(self, admin_session):
        """GET /api/admin/stats returns user count, transaction count, expert request breakdown"""
        response = admin_session.get(f"{BASE_URL}/api/admin/stats")
        assert response.status_code == 200, f"Stats failed: {response.text}"
        data = response.json()
        
        # Verify required fields
        assert "total_users" in data, "Missing total_users"
        assert "total_transactions" in data, "Missing total_transactions"
        assert "expert_requests" in data, "Missing expert_requests"
        
        # Verify expert_requests breakdown
        er = data["expert_requests"]
        assert "total" in er, "Missing expert_requests.total"
        assert "pending" in er, "Missing expert_requests.pending"
        assert "matched" in er, "Missing expert_requests.matched"
        assert "completed" in er, "Missing expert_requests.completed"
        
        # Verify plan_breakdown
        assert "plan_breakdown" in data, "Missing plan_breakdown"
        
        print(f"✓ Admin stats: {data['total_users']} users, {data['total_transactions']} transactions")
        print(f"  Expert requests: {er['total']} total, {er['pending']} pending, {er['matched']} matched")


class TestExpertRequestManagement:
    """Expert request CRUD operations"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return session
    
    def test_list_all_expert_requests(self, admin_session):
        """GET /api/admin/expert-requests returns list of all requests"""
        response = admin_session.get(f"{BASE_URL}/api/admin/expert-requests")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "requests" in data, "Missing requests field"
        assert "count" in data, "Missing count field"
        assert isinstance(data["requests"], list), "requests should be a list"
        
        print(f"✓ Listed {data['count']} expert requests")
        return data["requests"]
    
    def test_filter_expert_requests_by_status(self, admin_session):
        """GET /api/admin/expert-requests?status=pending returns filtered requests"""
        response = admin_session.get(f"{BASE_URL}/api/admin/expert-requests?status=pending")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # All returned requests should have status=pending
        for req in data["requests"]:
            assert req.get("status") == "pending", f"Expected pending, got {req.get('status')}"
        
        print(f"✓ Filtered to {data['count']} pending requests")
    
    def test_update_request_status_to_reviewing(self, admin_session):
        """PUT /api/admin/expert-requests/{id}/status with status=reviewing updates status"""
        # First get a request to update
        list_response = admin_session.get(f"{BASE_URL}/api/admin/expert-requests")
        requests_list = list_response.json().get("requests", [])
        
        if not requests_list:
            pytest.skip("No expert requests available to test status update")
        
        # Find a pending request or use first one
        test_request = None
        for req in requests_list:
            if req.get("status") == "pending":
                test_request = req
                break
        
        if not test_request:
            test_request = requests_list[0]
        
        request_id = test_request["id"]
        
        # Update to reviewing
        response = admin_session.put(
            f"{BASE_URL}/api/admin/expert-requests/{request_id}/status",
            json={"status": "reviewing"}
        )
        assert response.status_code == 200, f"Status update failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"✓ Updated request {request_id} to reviewing")
    
    def test_match_expert_with_details(self, admin_session):
        """PUT /api/admin/expert-requests/{id}/status with matched + expert details creates match"""
        # Get a request to match
        list_response = admin_session.get(f"{BASE_URL}/api/admin/expert-requests")
        requests_list = list_response.json().get("requests", [])
        
        if not requests_list:
            pytest.skip("No expert requests available to test matching")
        
        # Find a non-matched, non-completed request
        test_request = None
        for req in requests_list:
            if req.get("status") not in ["matched", "completed"]:
                test_request = req
                break
        
        if not test_request:
            pytest.skip("No suitable request for matching test")
        
        request_id = test_request["id"]
        
        # Match with expert details
        response = admin_session.put(
            f"{BASE_URL}/api/admin/expert-requests/{request_id}/status",
            json={
                "status": "matched",
                "expert_name": "TEST_Expert John Doe",
                "expert_email": "test_expert@example.com",
                "expert_phone": "+234-800-TEST",
                "expert_specialty": "Corporate Tax"
            }
        )
        assert response.status_code == 200, f"Match failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"✓ Matched request {request_id} with expert")
    
    def test_add_admin_note(self, admin_session):
        """POST /api/admin/expert-requests/{id}/note adds admin note"""
        # Get a request to add note to
        list_response = admin_session.get(f"{BASE_URL}/api/admin/expert-requests")
        requests_list = list_response.json().get("requests", [])
        
        if not requests_list:
            pytest.skip("No expert requests available to test notes")
        
        request_id = requests_list[0]["id"]
        
        # Add note
        response = admin_session.post(
            f"{BASE_URL}/api/admin/expert-requests/{request_id}/note",
            json={"note": f"TEST_Admin note added at {uuid.uuid4().hex[:8]}"}
        )
        assert response.status_code == 200, f"Add note failed: {response.text}"
        data = response.json()
        assert "message" in data
        assert "note" in data
        assert "id" in data["note"]
        assert "text" in data["note"]
        print(f"✓ Added admin note to request {request_id}")


class TestUserManagement:
    """User listing and plan updates"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return session
    
    def test_list_users_without_password_hash(self, admin_session):
        """GET /api/admin/users returns user list without password_hash"""
        response = admin_session.get(f"{BASE_URL}/api/admin/users")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "users" in data, "Missing users field"
        assert "count" in data, "Missing count field"
        assert isinstance(data["users"], list), "users should be a list"
        
        # Verify no password_hash in any user
        for user in data["users"]:
            assert "password_hash" not in user, "password_hash should not be exposed"
            assert "id" in user, "User should have id"
            assert "email" in user, "User should have email"
        
        print(f"✓ Listed {data['count']} users (no password_hash exposed)")
    
    def test_update_user_plan(self, admin_session):
        """PUT /api/admin/users/{id}/plan updates user subscription plan"""
        # Get users list
        list_response = admin_session.get(f"{BASE_URL}/api/admin/users")
        users_list = list_response.json().get("users", [])
        
        if len(users_list) < 2:
            pytest.skip("Need at least 2 users to test plan update (avoid updating admin)")
        
        # Find a non-admin user to update
        test_user = None
        for user in users_list:
            if user.get("role") != "admin":
                test_user = user
                break
        
        if not test_user:
            pytest.skip("No non-admin user available for plan update test")
        
        user_id = test_user["id"]
        current_plan = test_user.get("subscription_plan", "starter")
        new_plan = "pro" if current_plan != "pro" else "starter"
        
        # Update plan
        response = admin_session.put(
            f"{BASE_URL}/api/admin/users/{user_id}/plan",
            json={"plan": new_plan}
        )
        assert response.status_code == 200, f"Plan update failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"✓ Updated user {user_id} plan to {new_plan}")


class TestNonAdminAccess:
    """Verify non-admin users get 403 on admin endpoints"""
    
    @pytest.fixture(scope="class")
    def regular_user_session(self):
        """Create and login as a regular user"""
        session = requests.Session()
        
        # Register a new user
        register_response = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "name": TEST_USER_NAME,
            "business_type": "freelancer",
            "monthly_income_range": "100000-500000"
        })
        
        if register_response.status_code == 400 and "already registered" in register_response.text:
            # User exists, try login
            login_response = session.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
            if login_response.status_code != 200:
                pytest.skip("Could not create or login as test user")
        elif register_response.status_code != 200:
            pytest.skip(f"Could not register test user: {register_response.text}")
        
        return session
    
    def test_non_admin_gets_403_on_stats(self, regular_user_session):
        """Non-admin user gets 403 on GET /api/admin/stats"""
        response = regular_user_session.get(f"{BASE_URL}/api/admin/stats")
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Non-admin correctly denied access to /api/admin/stats")
    
    def test_non_admin_gets_403_on_expert_requests(self, regular_user_session):
        """Non-admin user gets 403 on GET /api/admin/expert-requests"""
        response = regular_user_session.get(f"{BASE_URL}/api/admin/expert-requests")
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Non-admin correctly denied access to /api/admin/expert-requests")
    
    def test_non_admin_gets_403_on_users(self, regular_user_session):
        """Non-admin user gets 403 on GET /api/admin/users"""
        response = regular_user_session.get(f"{BASE_URL}/api/admin/users")
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Non-admin correctly denied access to /api/admin/users")


class TestInvalidStatusValues:
    """Test validation of status values"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return session
    
    def test_invalid_status_returns_400(self, admin_session):
        """PUT with invalid status returns 400"""
        # Get a request
        list_response = admin_session.get(f"{BASE_URL}/api/admin/expert-requests")
        requests_list = list_response.json().get("requests", [])
        
        if not requests_list:
            pytest.skip("No expert requests available")
        
        request_id = requests_list[0]["id"]
        
        response = admin_session.put(
            f"{BASE_URL}/api/admin/expert-requests/{request_id}/status",
            json={"status": "invalid_status"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Invalid status correctly rejected with 400")
    
    def test_invalid_plan_returns_400(self, admin_session):
        """PUT with invalid plan returns 400"""
        # Get users
        list_response = admin_session.get(f"{BASE_URL}/api/admin/users")
        users_list = list_response.json().get("users", [])
        
        if not users_list:
            pytest.skip("No users available")
        
        user_id = users_list[0]["id"]
        
        response = admin_session.put(
            f"{BASE_URL}/api/admin/users/{user_id}/plan",
            json={"plan": "invalid_plan"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Invalid plan correctly rejected with 400")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
