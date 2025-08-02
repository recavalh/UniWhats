import requests
import sys
from datetime import datetime
import json

class UniWhatsDeskAPITester:
    def __init__(self, base_url="https://be14f64f-f2cc-4392-888a-6a11189fd1f5.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        # Add auth token if available
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                    elif isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            return success, response.json() if success and response.text else {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout")
            return False, {}
        except requests.exceptions.ConnectionError:
            print(f"❌ Failed - Connection error")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_login(self, email="admin@school.com", password="admin123"):
        """Test login functionality"""
        success, response = self.run_test(
            "Login Authentication",
            "POST",
            "api/auth/login",
            200,
            data={"email": email, "password": password}
        )
        
        if success and 'token' in response:
            self.auth_token = response['token']
            print(f"   ✓ Login successful for {email}")
            print(f"   ✓ Token received: {self.auth_token[:20]}...")
            if 'user' in response:
                user = response['user']
                print(f"   ✓ User: {user.get('name')} ({user.get('role')})")
        
        return success, response

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        success, response = self.run_test(
            "Login with Invalid Credentials",
            "POST",
            "api/auth/login",
            401,
            data={"email": "invalid@test.com", "password": "wrongpassword"}
        )
        
        if not success and response.get('detail'):
            print(f"   ✓ Proper error message: {response['detail']}")
        
        return not success  # We expect this to fail

    def test_forgot_password(self, email="admin@school.com"):
        """Test forgot password functionality"""
        success, response = self.run_test(
            "Forgot Password",
            "POST",
            "api/auth/forgot-password",
            200,
            data={"email": email}
        )
        
        if success and response.get('success'):
            print(f"   ✓ Password reset initiated for {email}")
            if 'temp_password' in response:
                print(f"   ✓ Temporary password: {response['temp_password']}")
        
        return success, response

    def test_logout(self):
        """Test logout functionality"""
        success, response = self.run_test(
            "Logout",
            "POST",
            "api/auth/logout",
            200
        )
        
        if success and response.get('success'):
            print(f"   ✓ Logout successful")
            # Clear token after logout
            self.auth_token = None
        
        return success, response

    def test_department_toggle(self, dept_id):
        """Test department activation toggle"""
        success, response = self.run_test(
            f"Toggle Department Status ({dept_id})",
            "POST",
            f"api/admin/departments/{dept_id}/toggle",
            200
        )
        
        if success:
            print(f"   ✓ Department {dept_id} status toggled successfully")
        
        return success, response

    def test_health_check(self):
        """Test basic health endpoint"""
        return self.run_test("Health Check", "GET", "api/test", 200)

    def test_get_departments(self):
        """Test departments endpoint"""
        success, response = self.run_test("Get Departments", "GET", "api/departments", 200)
        if success and isinstance(response, list):
            print(f"   Found {len(response)} departments")
            expected_departments = ["Reception & Finance", "Coordination", "Sales", "Management"]
            dept_names = [dept.get('name', '') for dept in response]
            for expected in expected_departments:
                if expected in dept_names:
                    print(f"   ✓ Found department: {expected}")
                else:
                    print(f"   ⚠ Missing department: {expected}")
        return success, response

    def test_get_users(self):
        """Test users endpoint"""
        success, response = self.run_test("Get Users", "GET", "api/users", 200)
        if success and isinstance(response, list):
            print(f"   Found {len(response)} users")
            expected_users = ["Maria Silva", "Carlos Santos", "Ana Costa", "João Diretor"]
            user_names = [user.get('name', '') for user in response]
            for expected in expected_users:
                if expected in user_names:
                    print(f"   ✓ Found user: {expected}")
                else:
                    print(f"   ⚠ Missing user: {expected}")
        return success, response

    def test_get_current_user(self):
        """Test current user endpoint"""
        success, response = self.run_test("Get Current User", "GET", "api/auth/me", 200)
        if success and isinstance(response, dict):
            print(f"   Current user: {response.get('name', 'Unknown')}")
            print(f"   Role: {response.get('role', 'Unknown')}")
        return success, response

    def test_get_conversations(self):
        """Test conversations endpoint"""
        success, response = self.run_test("Get Conversations", "GET", "api/conversations", 200)
        if success and isinstance(response, list):
            print(f"   Found {len(response)} conversations")
            expected_contacts = ["Patricia Almeida", "Roberto Fernandes", "Amanda Silva"]
            for i, conv in enumerate(response):
                contact_name = conv.get('contact', {}).get('name', 'Unknown')
                dept_name = conv.get('department', {}).get('name', 'Unknown')
                status = conv.get('status', 'Unknown')
                unread = conv.get('unread_count', 0)
                print(f"   Conv {i+1}: {contact_name} | {dept_name} | {status} | {unread} unread")
                
                if contact_name in expected_contacts:
                    print(f"   ✓ Found expected contact: {contact_name}")
        return success, response

    def test_get_messages(self, conversation_id):
        """Test messages endpoint for a specific conversation"""
        success, response = self.run_test(
            f"Get Messages for {conversation_id}", 
            "GET", 
            f"api/conversations/{conversation_id}/messages", 
            200
        )
        if success and isinstance(response, list):
            print(f"   Found {len(response)} messages")
            for i, msg in enumerate(response):
                direction = msg.get('direction', 'unknown')
                msg_type = msg.get('type', 'text')
                body = msg.get('body', '')[:50] + '...' if len(msg.get('body', '')) > 50 else msg.get('body', '')
                print(f"   Msg {i+1}: {direction} | {msg_type} | {body}")
        return success, response

    def test_send_message(self, conversation_id):
        """Test sending a message"""
        test_message = f"Test message sent at {datetime.now().strftime('%H:%M:%S')}"
        success, response = self.run_test(
            f"Send Message to {conversation_id}",
            "POST",
            f"api/conversations/{conversation_id}/messages",
            200,
            data={
                "conversation_id": conversation_id,
                "body": test_message,
                "type": "text"
            }
        )
        if success:
            print(f"   Message sent: {test_message}")
        return success, response

    def test_assign_conversation(self, conversation_id, user_id):
        """Test assigning a conversation"""
        success, response = self.run_test(
            f"Assign Conversation {conversation_id}",
            "POST",
            f"api/conversations/{conversation_id}/assign",
            200,
            data={
                "assignee_user_id": user_id
            }
        )
        return success, response

    def test_close_conversation(self, conversation_id):
        """Test closing a conversation"""
        success, response = self.run_test(
            f"Close Conversation {conversation_id}",
            "POST",
            f"api/conversations/{conversation_id}/close",
            200
        )
        return success, response

    def test_mark_messages_read(self, conversation_id):
        """Test marking messages as read"""
        success, response = self.run_test(
            f"Mark Messages Read {conversation_id}",
            "POST",
            f"api/conversations/{conversation_id}/mark-read",
            200
        )
        return success, response

def main():
    print("🚀 Starting UniWhats Desk API Tests")
    print("=" * 50)
    
    tester = UniWhatsDeskAPITester()
    
    # 🔐 AUTHENTICATION TESTS
    print("\n🔐 AUTHENTICATION TESTING")
    print("-" * 30)
    
    # Test login with valid credentials
    login_success, login_response = tester.test_login("admin@school.com", "admin123")
    
    # Test login with invalid credentials
    tester.test_login_invalid_credentials()
    
    # Test forgot password
    tester.test_forgot_password("admin@school.com")
    
    if not login_success:
        print("❌ Login failed - cannot continue with authenticated tests")
        return 1
    
    # Basic endpoint tests (now authenticated)
    print("\n📊 BASIC ENDPOINT TESTING")
    print("-" * 30)
    
    tester.test_health_check()
    
    # Test departments (should show both active and inactive)
    dept_success, departments = tester.test_get_departments()
    
    tester.test_get_users()
    tester.test_get_current_user()
    
    # 🏢 DEPARTMENT TOGGLE TESTING
    print("\n🏢 DEPARTMENT TOGGLE TESTING")
    print("-" * 30)
    
    if dept_success and departments:
        # Test department toggle functionality
        for dept in departments[:2]:  # Test first 2 departments
            dept_id = dept.get('id')
            dept_name = dept.get('name')
            current_status = dept.get('active', True)
            
            print(f"\n   Testing department: {dept_name} (currently {'active' if current_status else 'inactive'})")
            
            # Toggle department status
            toggle_success, _ = tester.test_department_toggle(dept_id)
            
            if toggle_success:
                # Verify the toggle worked by getting departments again
                _, updated_departments = tester.test_get_departments()
                if updated_departments:
                    updated_dept = next((d for d in updated_departments if d.get('id') == dept_id), None)
                    if updated_dept:
                        new_status = updated_dept.get('active', True)
                        if new_status != current_status:
                            print(f"   ✓ Department status changed: {current_status} → {new_status}")
                        else:
                            print(f"   ⚠ Department status unchanged after toggle")
    
    # 💬 CONVERSATION TESTS
    print("\n💬 CONVERSATION TESTING")
    print("-" * 30)
    
    success, conversations = tester.test_get_conversations()
    
    if success and conversations:
        # Test first conversation in detail
        first_conv = conversations[0]
        conv_id = first_conv.get('id')
        
        if conv_id:
            print(f"\n📋 Testing detailed functionality with conversation: {conv_id}")
            
            # Test messages
            tester.test_get_messages(conv_id)
            
            # Test sending message (for WebSocket testing)
            tester.test_send_message(conv_id)
            
            # Test mark as read
            tester.test_mark_messages_read(conv_id)
            
            # Test assignment (if we have users)
            _, users = tester.test_get_users()
            if users and len(users) > 0:
                user_id = users[0].get('id')
                if user_id:
                    tester.test_assign_conversation(conv_id, user_id)
            
            # Test close conversation
            tester.test_close_conversation(conv_id)
    
    # 🚪 LOGOUT TEST
    print("\n🚪 LOGOUT TESTING")
    print("-" * 30)
    
    tester.test_logout()
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())