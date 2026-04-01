#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class NairaTrackAPITester:
    def __init__(self, base_url: str = "https://tax-naira.preview.emergentagent.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_token = None
        self.test_user_token = None
        self.test_user_id = None
        self.test_transaction_id = None
        self.test_bank_account_id = None

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    files: Optional[Dict] = None, use_admin: bool = False) -> tuple[bool, Dict]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}/api{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add auth token if available
        token = self.admin_token if use_admin else self.test_user_token
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers if token else None)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    headers.pop('Content-Type', None)
                    response = self.session.post(url, files=files, headers=headers if token else None)
                else:
                    response = self.session.post(url, json=data, headers=headers if token else None)
            elif method == 'PUT':
                response = self.session.put(url, json=data, headers=headers if token else None)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=headers if token else None)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            if response.status_code < 400:
                try:
                    return True, response.json()
                except:
                    return True, {"message": "Success", "status_code": response.status_code}
            else:
                try:
                    error_data = response.json()
                except:
                    error_data = {"error": response.text, "status_code": response.status_code}
                return False, error_data

        except Exception as e:
            return False, {"error": str(e)}

    def test_health_check(self):
        """Test basic health endpoints"""
        success, data = self.make_request('GET', '/')
        self.log_test("API Root Health Check", success, f"- {data.get('message', '')}")
        
        success, data = self.make_request('GET', '/health')
        self.log_test("API Health Endpoint", success, f"- Status: {data.get('status', 'unknown')}")

    def test_admin_login(self):
        """Test admin login"""
        login_data = {
            "email": "admin@nairatrack.ng",
            "password": "NairaTrack2024!"
        }
        success, data = self.make_request('POST', '/auth/login', login_data)
        if success and 'id' in data:
            # Extract token from cookies if available
            self.admin_token = None  # Will use cookies instead
            self.log_test("Admin Login", True, f"- Admin ID: {data['id']}")
            return True
        else:
            self.log_test("Admin Login", False, f"- Error: {data.get('detail', 'Unknown error')}")
            return False

    def test_user_registration(self):
        """Test user registration"""
        timestamp = datetime.now().strftime("%H%M%S")
        register_data = {
            "name": f"Test User {timestamp}",
            "email": f"testuser{timestamp}@example.com",
            "password": "TestPass123!",
            "business_type": "freelancer",
            "monthly_income_range": "100000-500000"
        }
        
        success, data = self.make_request('POST', '/auth/register', register_data)
        if success and 'id' in data:
            self.test_user_id = data['id']
            self.test_user_email = register_data['email']
            self.log_test("User Registration", True, f"- User ID: {data['id']}")
            return True
        else:
            self.log_test("User Registration", False, f"- Error: {data.get('detail', 'Unknown error')}")
            return False

    def test_user_login(self):
        """Test user login"""
        if not hasattr(self, 'test_user_email'):
            self.log_test("User Login", False, "- No test user email available")
            return False
            
        login_data = {
            "email": self.test_user_email,
            "password": "TestPass123!"
        }
        success, data = self.make_request('POST', '/auth/login', login_data)
        if success and 'id' in data:
            self.test_user_token = None  # Will use cookies
            self.log_test("User Login", True, f"- User ID: {data['id']}")
            return True
        else:
            self.log_test("User Login", False, f"- Error: {data.get('detail', 'Unknown error')}")
            return False

    def test_get_me(self):
        """Test get current user"""
        success, data = self.make_request('GET', '/auth/me')
        self.log_test("Get Current User", success, f"- Name: {data.get('name', 'N/A')}")

    def test_dashboard(self):
        """Test dashboard endpoint"""
        success, data = self.make_request('GET', '/dashboard')
        if success:
            details = f"- Income: ₦{data.get('total_income', 0):,.0f}, Tax Score: {data.get('tax_health_score', 0)}"
            self.log_test("Dashboard Data", True, details)
        else:
            self.log_test("Dashboard Data", False, f"- Error: {data.get('detail', 'Unknown error')}")

    def test_categories(self):
        """Test categories endpoint"""
        success, data = self.make_request('GET', '/categories')
        if success and 'income' in data and 'expense' in data:
            income_count = len(data['income'])
            expense_count = len(data['expense'])
            self.log_test("Categories", True, f"- Income: {income_count}, Expense: {expense_count}")
        else:
            self.log_test("Categories", False, f"- Error: {data.get('detail', 'Invalid response')}")

    def test_create_transaction(self):
        """Test transaction creation"""
        transaction_data = {
            "amount": 50000,
            "type": "income",
            "category": "Sales",
            "description": "Test income transaction",
            "date": datetime.now().isoformat()
        }
        
        success, data = self.make_request('POST', '/transactions', transaction_data)
        if success and 'id' in data:
            self.test_transaction_id = data['id']
            self.log_test("Create Transaction", True, f"- Transaction ID: {data['id']}")
            return True
        else:
            self.log_test("Create Transaction", False, f"- Error: {data.get('detail', 'Unknown error')}")
            return False

    def test_get_transactions(self):
        """Test get transactions"""
        success, data = self.make_request('GET', '/transactions')
        if success and isinstance(data, list):
            self.log_test("Get Transactions", True, f"- Count: {len(data)}")
        else:
            self.log_test("Get Transactions", False, f"- Error: {data.get('detail', 'Invalid response')}")

    def test_tax_calculation(self):
        """Test tax calculation"""
        success, data = self.make_request('GET', '/tax-calculation')
        if success and 'gross_income' in data:
            details = f"- Gross: ₦{data.get('gross_income', 0):,.0f}, Tax: ₦{data.get('income_tax', 0):,.0f}"
            self.log_test("Tax Calculation", True, details)
        else:
            self.log_test("Tax Calculation", False, f"- Error: {data.get('detail', 'Unknown error')}")

    def test_supported_banks(self):
        """Test supported banks endpoint"""
        success, data = self.make_request('GET', '/banks')
        if success and 'banks' in data:
            bank_count = len(data['banks'])
            self.log_test("Supported Banks", True, f"- Count: {bank_count}")
        else:
            self.log_test("Supported Banks", False, f"- Error: {data.get('detail', 'Unknown error')}")

    def test_bank_account_linking(self):
        """Test bank account linking (requires Growth+ plan)"""
        # First upgrade to Growth plan
        upgrade_data = {"plan": "growth"}
        success, _ = self.make_request('PUT', '/user/subscription', upgrade_data)
        
        if success:
            bank_data = {
                "bank_name": "GTBank",
                "account_number": "0123456789",
                "account_name": "Test User Account"
            }
            
            success, data = self.make_request('POST', '/bank-accounts', bank_data)
            if success and 'id' in data:
                self.test_bank_account_id = data['id']
                self.log_test("Bank Account Linking", True, f"- Account ID: {data['id']}")
                return True
            else:
                self.log_test("Bank Account Linking", False, f"- Error: {data.get('detail', 'Unknown error')}")
        else:
            self.log_test("Bank Account Linking", False, "- Failed to upgrade plan")
        return False

    def test_get_bank_accounts(self):
        """Test get bank accounts"""
        success, data = self.make_request('GET', '/bank-accounts')
        if success and isinstance(data, list):
            self.log_test("Get Bank Accounts", True, f"- Count: {len(data)}")
        else:
            self.log_test("Get Bank Accounts", False, f"- Error: {data.get('detail', 'Invalid response')}")

    def test_ai_chat(self):
        """Test AI chat assistant"""
        chat_data = {
            "message": "What is PITA tax rate for ₦500,000 income?",
            "session_id": f"test-session-{datetime.now().strftime('%H%M%S')}"
        }
        
        success, data = self.make_request('POST', '/chat', chat_data)
        if success and 'response' in data:
            response_preview = data['response'][:100] + "..." if len(data['response']) > 100 else data['response']
            self.log_test("AI Chat Assistant", True, f"- Response: {response_preview}")
        else:
            self.log_test("AI Chat Assistant", False, f"- Error: {data.get('detail', 'Unknown error')}")

    def test_tax_filing_guide(self):
        """Test tax filing guide"""
        success, data = self.make_request('GET', '/tax-filing/guide')
        if success and 'steps' in data:
            step_count = len(data['steps'])
            self.log_test("Tax Filing Guide", True, f"- Steps: {step_count}")
        else:
            self.log_test("Tax Filing Guide", False, f"- Error: {data.get('detail', 'Unknown error')}")

    def test_filing_checklist(self):
        """Test filing checklist"""
        success, data = self.make_request('GET', '/tax-filing/checklist')
        if success and 'checklist' in data:
            progress = data.get('progress_percentage', 0)
            self.log_test("Filing Checklist", True, f"- Progress: {progress}%")
        else:
            self.log_test("Filing Checklist", False, f"- Error: {data.get('detail', 'Unknown error')}")

    def test_education_articles(self):
        """Test education articles"""
        success, data = self.make_request('GET', '/education/articles')
        if success and isinstance(data, list):
            self.log_test("Education Articles", True, f"- Count: {len(data)}")
        else:
            self.log_test("Education Articles", False, f"- Error: {data.get('detail', 'Invalid response')}")

    def test_reports_summary(self):
        """Test reports summary"""
        success, data = self.make_request('GET', '/reports/summary?period=month')
        if success and 'total_income' in data:
            income = data.get('total_income', 0)
            self.log_test("Reports Summary", True, f"- Monthly Income: ₦{income:,.0f}")
        else:
            self.log_test("Reports Summary", False, f"- Error: {data.get('detail', 'Unknown error')}")

    def test_user_settings_update(self):
        """Test user settings update"""
        settings_data = {"pidgin_mode": True}
        success, data = self.make_request('PUT', '/user/settings', settings_data)
        self.log_test("User Settings Update", success, f"- Pidgin mode enabled")

    def test_logout(self):
        """Test logout"""
        success, data = self.make_request('POST', '/auth/logout')
        self.log_test("User Logout", success, f"- {data.get('message', 'Logged out')}")

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting NairaTrack Backend API Tests")
        print("=" * 50)
        
        # Health checks
        self.test_health_check()
        
        # Authentication flow
        self.test_admin_login()
        self.test_user_registration()
        self.test_user_login()
        self.test_get_me()
        
        # Core functionality
        self.test_dashboard()
        self.test_categories()
        self.test_create_transaction()
        self.test_get_transactions()
        self.test_tax_calculation()
        
        # Bank integration
        self.test_supported_banks()
        self.test_bank_account_linking()
        self.test_get_bank_accounts()
        
        # AI and guidance
        self.test_ai_chat()
        self.test_tax_filing_guide()
        self.test_filing_checklist()
        self.test_education_articles()
        
        # Reports and settings
        self.test_reports_summary()
        self.test_user_settings_update()
        
        # Cleanup
        self.test_logout()
        
        # Summary
        print("\n" + "=" * 50)
        print(f"📊 Backend Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"✨ Success Rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test runner"""
    tester = NairaTrackAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())