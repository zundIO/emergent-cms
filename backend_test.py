#!/usr/bin/env python3
"""
Backend API Testing for The Monolith CMS
Tests all authentication and pages endpoints
"""
import requests
import sys
import json
from datetime import datetime

class MonolithCMSAPITester:
    def __init__(self, base_url="https://page-studio-71.preview.emergentagent.com"):
        self.base_url = base_url
        self.admin_token = None
        self.editor_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            details = f"Expected {expected_status}, got {response.status_code}"
            if not success:
                try:
                    error_data = response.json()
                    details += f" - {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f" - {response.text[:100]}"
            
            self.log_test(name, success, details if not success else "")
            return success, response.json() if success and response.content else {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        print("\n🔍 Testing Health Check...")
        success, response = self.run_test(
            "Health Check",
            "GET",
            "api/health",
            200
        )
        return success

    def test_admin_login(self):
        """Test admin login"""
        print("\n🔍 Testing Admin Authentication...")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "api/auth/login",
            200,
            data={"email": "admin@monolith.cms", "password": "admin123"}
        )
        if success and 'token' in response:
            self.admin_token = response['token']
            print(f"   Admin token obtained: {self.admin_token[:20]}...")
            return True
        return False

    def test_editor_login(self):
        """Test editor login"""
        print("\n🔍 Testing Editor Authentication...")
        success, response = self.run_test(
            "Editor Login",
            "POST",
            "api/auth/login",
            200,
            data={"email": "editor@monolith.cms", "password": "editor123"}
        )
        if success and 'token' in response:
            self.editor_token = response['token']
            print(f"   Editor token obtained: {self.editor_token[:20]}...")
            return True
        return False

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        print("\n🔍 Testing Invalid Login...")
        success, response = self.run_test(
            "Invalid Login",
            "POST",
            "api/auth/login",
            401,
            data={"email": "wrong@email.com", "password": "wrongpass"}
        )
        return success

    def test_get_me(self):
        """Test get current user endpoint"""
        print("\n🔍 Testing Get Current User...")
        if not self.admin_token:
            self.log_test("Get Me", False, "No admin token available")
            return False
        
        success, response = self.run_test(
            "Get Me (Admin)",
            "GET",
            "api/auth/me",
            200,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        return success

    def test_pages_list(self):
        """Test pages list endpoint"""
        print("\n🔍 Testing Pages List...")
        if not self.admin_token:
            self.log_test("Pages List", False, "No admin token available")
            return False
        
        success, response = self.run_test(
            "Pages List",
            "GET",
            "api/pages",
            200,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        if success and isinstance(response, list) and len(response) > 0:
            print(f"   Found {len(response)} pages")
            self.homepage_id = None
            for page in response:
                if page.get('name') == 'Homepage':
                    self.homepage_id = page.get('_id')
                    print(f"   Homepage ID: {self.homepage_id}")
                    break
            return True
        return success

    def test_get_page(self):
        """Test get single page endpoint"""
        print("\n🔍 Testing Get Single Page...")
        if not self.admin_token or not hasattr(self, 'homepage_id') or not self.homepage_id:
            self.log_test("Get Page", False, "No admin token or homepage ID available")
            return False
        
        success, response = self.run_test(
            "Get Homepage",
            "GET",
            f"api/pages/{self.homepage_id}",
            200,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        if success and 'elements' in response:
            print(f"   Page has {len(response.get('elements', []))} elements")
            # Find a text element to test content update (search recursively)
            self.test_element_id = None
            
            def find_text_element(elements):
                for element in elements:
                    if element.get('type') in ['heading', 'paragraph'] and element.get('content', {}).get('text'):
                        return element.get('id')
                    if element.get('children'):
                        found = find_text_element(element['children'])
                        if found:
                            return found
                return None
            
            self.test_element_id = find_text_element(response.get('elements', []))
            if self.test_element_id:
                print(f"   Found test element: {self.test_element_id}")
            else:
                print("   No suitable text element found for testing")
            return True
        return success

    def test_update_content(self):
        """Test content update endpoint"""
        print("\n🔍 Testing Content Update...")
        if not self.admin_token or not hasattr(self, 'test_element_id') or not self.test_element_id:
            self.log_test("Update Content", False, "No admin token or test element ID available")
            return False
        
        test_text = f"Updated text at {datetime.now().strftime('%H:%M:%S')}"
        success, response = self.run_test(
            "Update Element Content",
            "PUT",
            f"api/pages/{self.homepage_id}/content",
            200,
            data={
                "element_id": self.test_element_id,
                "content": {"text": test_text}
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        return success

    def test_bulk_content_update(self):
        """Test bulk content update endpoint"""
        print("\n🔍 Testing Bulk Content Update...")
        if not self.admin_token or not hasattr(self, 'test_element_id') or not self.test_element_id:
            self.log_test("Bulk Update Content", False, "No admin token or test element ID available")
            return False
        
        test_text = f"Bulk updated text at {datetime.now().strftime('%H:%M:%S')}"
        success, response = self.run_test(
            "Bulk Update Content",
            "PUT",
            f"api/pages/{self.homepage_id}/content/bulk",
            200,
            data={
                "updates": [
                    {
                        "element_id": self.test_element_id,
                        "content": {"text": test_text}
                    }
                ]
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        return success

    def test_publish_page(self):
        """Test page publishing"""
        print("\n🔍 Testing Page Publishing...")
        if not self.admin_token or not hasattr(self, 'homepage_id') or not self.homepage_id:
            self.log_test("Publish Page", False, "No admin token or homepage ID available")
            return False
        
        success, response = self.run_test(
            "Publish Page",
            "PUT",
            f"api/pages/{self.homepage_id}/status",
            200,
            data={"status": "published"},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        return success

    def test_public_pages(self):
        """Test public pages endpoint"""
        print("\n🔍 Testing Public Pages...")
        success, response = self.run_test(
            "Public Pages List",
            "GET",
            "api/public/pages",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} published pages")
            return True
        return success

    def test_public_page_by_slug(self):
        """Test public page by slug"""
        print("\n🔍 Testing Public Page by Slug...")
        success, response = self.run_test(
            "Public Homepage by Slug",
            "GET",
            "api/public/pages/",
            200
        )
        return success

    def test_unauthorized_access(self):
        """Test unauthorized access"""
        print("\n🔍 Testing Unauthorized Access...")
        success, response = self.run_test(
            "Unauthorized Pages Access",
            "GET",
            "api/pages",
            401
        )
        return success

    # ============================================================
    # PHASE 3 TESTS: USER MANAGEMENT
    # ============================================================

    def test_list_users(self):
        """Test list users endpoint (admin only)"""
        print("\n🔍 Testing List Users (Admin Only)...")
        if not self.admin_token:
            self.log_test("List Users", False, "No admin token available")
            return False
        
        success, response = self.run_test(
            "List Users",
            "GET",
            "api/users",
            200,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} users")
            # Store user IDs for further testing
            self.test_users = response
            return True
        return success

    def test_list_users_as_editor(self):
        """Test list users endpoint as editor (should fail)"""
        print("\n🔍 Testing List Users as Editor (Should Fail)...")
        if not self.editor_token:
            self.log_test("List Users as Editor", False, "No editor token available")
            return False
        
        success, response = self.run_test(
            "List Users as Editor (403 Expected)",
            "GET",
            "api/users",
            403,
            headers={"Authorization": f"Bearer {self.editor_token}"}
        )
        return success

    def test_create_user(self):
        """Test create user endpoint"""
        print("\n🔍 Testing Create User...")
        if not self.admin_token:
            self.log_test("Create User", False, "No admin token available")
            return False
        
        test_email = f"test.user.{datetime.now().strftime('%H%M%S')}@monolith.cms"
        success, response = self.run_test(
            "Create User",
            "POST",
            "api/auth/register",
            200,
            data={
                "email": test_email,
                "password": "testpass123",
                "name": "Test User",
                "role": "editor"
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        if success and 'id' in response:
            self.created_user_id = response['id']
            self.created_user_email = test_email
            print(f"   Created user ID: {self.created_user_id}")
            return True
        return success

    def test_update_user(self):
        """Test update user endpoint"""
        print("\n🔍 Testing Update User...")
        if not self.admin_token or not hasattr(self, 'created_user_id'):
            self.log_test("Update User", False, "No admin token or created user ID available")
            return False
        
        success, response = self.run_test(
            "Update User Name and Role",
            "PUT",
            f"api/users/{self.created_user_id}",
            200,
            data={
                "name": "Updated Test User",
                "role": "admin"
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        return success

    def test_change_user_password(self):
        """Test change user password endpoint"""
        print("\n🔍 Testing Change User Password...")
        if not self.admin_token or not hasattr(self, 'created_user_id'):
            self.log_test("Change User Password", False, "No admin token or created user ID available")
            return False
        
        success, response = self.run_test(
            "Change User Password",
            "PUT",
            f"api/users/{self.created_user_id}/password",
            200,
            data={"new_password": "newpassword123"},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        return success

    def test_disable_user(self):
        """Test disable user (set is_active=false)"""
        print("\n🔍 Testing Disable User...")
        if not self.admin_token or not hasattr(self, 'created_user_id'):
            self.log_test("Disable User", False, "No admin token or created user ID available")
            return False
        
        success, response = self.run_test(
            "Disable User",
            "PUT",
            f"api/users/{self.created_user_id}",
            200,
            data={"is_active": False},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        return success

    def test_disabled_user_login(self):
        """Test that disabled user cannot login"""
        print("\n🔍 Testing Disabled User Login (Should Fail)...")
        if not hasattr(self, 'created_user_email'):
            self.log_test("Disabled User Login", False, "No created user email available")
            return False
        
        success, response = self.run_test(
            "Disabled User Login (403 Expected)",
            "POST",
            "api/auth/login",
            403,
            data={"email": self.created_user_email, "password": "newpassword123"}
        )
        return success

    def test_delete_user(self):
        """Test delete user endpoint"""
        print("\n🔍 Testing Delete User...")
        if not self.admin_token or not hasattr(self, 'created_user_id'):
            self.log_test("Delete User", False, "No admin token or created user ID available")
            return False
        
        success, response = self.run_test(
            "Delete User",
            "DELETE",
            f"api/users/{self.created_user_id}",
            200,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        return success

    # ============================================================
    # PHASE 3 TESTS: VERSION HISTORY
    # ============================================================

    def test_list_page_versions(self):
        """Test list page versions endpoint"""
        print("\n🔍 Testing List Page Versions...")
        if not self.admin_token or not hasattr(self, 'homepage_id'):
            self.log_test("List Page Versions", False, "No admin token or homepage ID available")
            return False
        
        success, response = self.run_test(
            "List Page Versions",
            "GET",
            f"api/pages/{self.homepage_id}/versions",
            200,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} versions")
            if len(response) > 0:
                self.latest_version = response[0]['version_number']
                print(f"   Latest version: {self.latest_version}")
            return True
        return success

    def test_get_page_version(self):
        """Test get specific page version"""
        print("\n🔍 Testing Get Page Version...")
        if not self.admin_token or not hasattr(self, 'homepage_id') or not hasattr(self, 'latest_version'):
            self.log_test("Get Page Version", False, "No admin token, homepage ID, or version available")
            return False
        
        success, response = self.run_test(
            f"Get Page Version {self.latest_version}",
            "GET",
            f"api/pages/{self.homepage_id}/versions/{self.latest_version}",
            200,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        if success and 'elements' in response:
            print(f"   Version has {len(response.get('elements', []))} elements")
            return True
        return success

    def test_restore_page_version(self):
        """Test restore page to previous version"""
        print("\n🔍 Testing Restore Page Version...")
        if not self.admin_token or not hasattr(self, 'homepage_id') or not hasattr(self, 'latest_version'):
            self.log_test("Restore Page Version", False, "No admin token, homepage ID, or version available")
            return False
        
        success, response = self.run_test(
            f"Restore Page to Version {self.latest_version}",
            "POST",
            f"api/pages/{self.homepage_id}/versions/{self.latest_version}/restore",
            200,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        if success and 'elements' in response:
            print(f"   Restored page has {len(response.get('elements', []))} elements")
            return True
        return success

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Monolith CMS Backend API Tests - Phase 3")
        print(f"Testing against: {self.base_url}")
        
        # Health check
        if not self.test_health_check():
            print("❌ Health check failed - stopping tests")
            return False
        
        # Authentication tests
        admin_login_ok = self.test_admin_login()
        editor_login_ok = self.test_editor_login()
        self.test_invalid_login()
        
        if not admin_login_ok:
            print("❌ Admin login failed - stopping tests")
            return False
        
        # Authenticated endpoints
        self.test_get_me()
        self.test_unauthorized_access()
        
        # Pages tests
        if self.test_pages_list():
            if self.test_get_page():
                self.test_update_content()
                self.test_bulk_content_update()
                self.test_publish_page()
        
        # Public endpoints
        self.test_public_pages()
        self.test_public_page_by_slug()
        
        # PHASE 3: User Management Tests
        print("\n" + "="*50)
        print("🔐 PHASE 3: USER MANAGEMENT TESTS")
        print("="*50)
        
        self.test_list_users()
        if editor_login_ok:
            self.test_list_users_as_editor()
        
        if self.test_create_user():
            self.test_update_user()
            self.test_change_user_password()
            self.test_disable_user()
            self.test_disabled_user_login()
            self.test_delete_user()
        
        # PHASE 3: Version History Tests
        print("\n" + "="*50)
        print("📚 PHASE 3: VERSION HISTORY TESTS")
        print("="*50)
        
        if self.test_list_page_versions():
            self.test_get_page_version()
            self.test_restore_page_version()
        
        return True

    def print_summary(self):
        """Print test summary"""
        print(f"\n📊 Test Summary:")
        print(f"   Tests run: {self.tests_run}")
        print(f"   Tests passed: {self.tests_passed}")
        print(f"   Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed < self.tests_run:
            print(f"\n❌ Failed tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = MonolithCMSAPITester()
    
    try:
        tester.run_all_tests()
        success = tester.print_summary()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())