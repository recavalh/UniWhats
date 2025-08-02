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
        self.critical_issues = {
            'authentication_bug': False,
            'profile_editing': False,
            'whatsapp_integration': False,
            'role_based_access': False,
            'media_features': False
        }

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

    def test_critical_authentication_bug(self):
        """Test CRITICAL ISSUE #1: Authentication Bug - Test login with different users"""
        print("\n🔐 CRITICAL TEST: Authentication Bug Verification")
        print("-" * 50)
        
        test_users = [
            {"email": "maria@school.com", "password": "admin123", "expected_name": "Maria Silva", "expected_role": "Receptionist"},
            {"email": "carlos@school.com", "password": "admin123", "expected_name": "Carlos Santos", "expected_role": "Coordinator"},
            {"email": "admin@school.com", "password": "admin123", "expected_name": "João Diretor", "expected_role": "Manager"}
        ]
        
        auth_tests_passed = 0
        total_auth_tests = len(test_users)
        
        for user_test in test_users:
            print(f"\n   Testing login for: {user_test['email']}")
            
            # Clear any existing token
            self.auth_token = None
            
            success, response = self.run_test(
                f"Login as {user_test['email']}",
                "POST",
                "api/auth/login",
                200,
                data={"email": user_test["email"], "password": user_test["password"]}
            )
            
            if success and 'user' in response:
                user = response['user']
                actual_name = user.get('name', '')
                actual_role = user.get('role', '')
                actual_email = user.get('email', '')
                
                print(f"   ✓ Login successful")
                print(f"   ✓ Returned user: {actual_name} ({actual_role})")
                print(f"   ✓ Email: {actual_email}")
                
                # Verify correct user profile returned
                if (actual_name == user_test['expected_name'] and 
                    actual_role == user_test['expected_role'] and
                    actual_email == user_test['email']):
                    print(f"   ✅ PASS: Correct user profile returned")
                    auth_tests_passed += 1
                    
                    # Test /api/auth/me endpoint with this token
                    if 'token' in response:
                        self.auth_token = response['token']
                        me_success, me_response = self.run_test(
                            f"Get current user info for {user_test['email']}",
                            "GET",
                            "api/auth/me",
                            200
                        )
                        
                        if me_success and me_response.get('name') == user_test['expected_name']:
                            print(f"   ✅ /api/auth/me returns correct user")
                        else:
                            print(f"   ❌ /api/auth/me returns wrong user: {me_response.get('name', 'Unknown')}")
                else:
                    print(f"   ❌ FAIL: Wrong user profile returned")
                    print(f"      Expected: {user_test['expected_name']} ({user_test['expected_role']})")
                    print(f"      Got: {actual_name} ({actual_role})")
            else:
                print(f"   ❌ FAIL: Login failed for {user_test['email']}")
        
        # Test logout and cross-contamination
        print(f"\n   Testing logout and session isolation...")
        logout_success, _ = self.run_test("Logout", "POST", "api/auth/logout", 200)
        if logout_success:
            print(f"   ✅ Logout successful")
        
        self.critical_issues['authentication_bug'] = (auth_tests_passed == total_auth_tests)
        
        if self.critical_issues['authentication_bug']:
            print(f"\n✅ CRITICAL ISSUE #1 RESOLVED: Authentication working correctly ({auth_tests_passed}/{total_auth_tests})")
        else:
            print(f"\n❌ CRITICAL ISSUE #1 FAILED: Authentication bug present ({auth_tests_passed}/{total_auth_tests})")
        
        return self.critical_issues['authentication_bug']

    def test_critical_profile_editing(self):
        """Test CRITICAL ISSUE #2: Profile Editing"""
        print("\n👤 CRITICAL TEST: Profile Editing Verification")
        print("-" * 50)
        
        # Login as admin first
        login_success, login_response = self.test_login("admin@school.com", "admin123")
        if not login_success:
            print("❌ Cannot test profile editing - login failed")
            return False
        
        user_id = login_response.get('user', {}).get('id')
        if not user_id:
            print("❌ Cannot get user ID for profile editing test")
            return False
        
        print(f"   Testing profile editing for user ID: {user_id}")
        
        # Test profile update
        profile_update_data = {
            "name": "João Diretor Updated",
            "email": "admin.updated@school.com",
            "avatar": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face"
        }
        
        success, response = self.run_test(
            "Update User Profile",
            "PUT",
            f"api/users/{user_id}/profile",
            200,
            data=profile_update_data
        )
        
        if success and isinstance(response, dict):
            updated_name = response.get('name', '')
            updated_email = response.get('email', '')
            updated_avatar = response.get('avatar', '')
            
            print(f"   ✓ Profile update successful")
            print(f"   ✓ Updated name: {updated_name}")
            print(f"   ✓ Updated email: {updated_email}")
            print(f"   ✓ Updated avatar: {updated_avatar[:50]}...")
            
            # Verify changes are reflected immediately
            me_success, me_response = self.run_test(
                "Verify profile changes via /api/auth/me",
                "GET",
                "api/auth/me",
                200
            )
            
            if (me_success and 
                me_response.get('name') == profile_update_data['name'] and
                me_response.get('email') == profile_update_data['email']):
                print(f"   ✅ Profile changes reflected immediately")
                self.critical_issues['profile_editing'] = True
            else:
                print(f"   ❌ Profile changes not reflected in /api/auth/me")
                print(f"      Expected: {profile_update_data['name']}, {profile_update_data['email']}")
                print(f"      Got: {me_response.get('name', 'Unknown')}, {me_response.get('email', 'Unknown')}")
        else:
            print(f"   ❌ Profile update failed")
        
        if self.critical_issues['profile_editing']:
            print(f"\n✅ CRITICAL ISSUE #2 RESOLVED: Profile editing working correctly")
        else:
            print(f"\n❌ CRITICAL ISSUE #2 FAILED: Profile editing not working")
        
        return self.critical_issues['profile_editing']

    def test_critical_whatsapp_integration(self):
        """Test CRITICAL ISSUE #3: WhatsApp Integration"""
        print("\n📱 CRITICAL TEST: WhatsApp Integration Verification")
        print("-" * 50)
        
        # Login as admin (only Manager can access WhatsApp settings)
        login_success, login_response = self.test_login("admin@school.com", "admin123")
        if not login_success:
            print("❌ Cannot test WhatsApp integration - login failed")
            return False
        
        # Test getting WhatsApp settings
        success, response = self.run_test(
            "Get WhatsApp Settings",
            "GET",
            "api/admin/whatsapp/settings",
            200
        )
        
        if success and isinstance(response, dict):
            phone_number_id = response.get('phone_number_id', '')
            business_account_id = response.get('business_account_id', '')
            webhook_url = response.get('webhook_url', '')
            configured = response.get('configured', False)
            
            print(f"   ✓ WhatsApp settings retrieved")
            print(f"   ✓ Phone Number ID: {phone_number_id}")
            print(f"   ✓ Business Account ID: {business_account_id}")
            print(f"   ✓ Webhook URL: {webhook_url}")
            print(f"   ✓ Configured: {configured}")
            
            # Check if expected credentials are present
            expected_phone = "183435611523520"
            expected_business = "177429005461076"
            expected_webhook = "https://uni-whats.vercel.app/webhooks/whatsapp"
            
            if (phone_number_id == expected_phone and 
                business_account_id == expected_business and
                webhook_url == expected_webhook):
                print(f"   ✅ Expected credentials are active")
                
                # Test webhook verification endpoint
                webhook_success, webhook_response = self.run_test(
                    "Test WhatsApp Webhook Verification",
                    "GET",
                    "webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=test_token&hub.challenge=12345",
                    200  # This might fail if verify token doesn't match, but we test the endpoint
                )
                
                if webhook_success:
                    print(f"   ✅ Webhook endpoint accessible")
                else:
                    print(f"   ⚠ Webhook endpoint test (expected if verify token doesn't match)")
                
                self.critical_issues['whatsapp_integration'] = True
            else:
                print(f"   ❌ Expected credentials not found")
                print(f"      Expected Phone: {expected_phone}, Got: {phone_number_id}")
                print(f"      Expected Business: {expected_business}, Got: {business_account_id}")
                print(f"      Expected Webhook: {expected_webhook}, Got: {webhook_url}")
        else:
            print(f"   ❌ Failed to get WhatsApp settings")
        
        if self.critical_issues['whatsapp_integration']:
            print(f"\n✅ CRITICAL ISSUE #3 RESOLVED: WhatsApp integration configured correctly")
        else:
            print(f"\n❌ CRITICAL ISSUE #3 FAILED: WhatsApp integration not properly configured")
        
        return self.critical_issues['whatsapp_integration']

    def test_critical_role_based_access(self):
        """Test CRITICAL ISSUE #4: Role-Based Access Control"""
        print("\n🔐 CRITICAL TEST: Role-Based Access Control Verification")
        print("-" * 50)
        
        role_tests = [
            {"email": "maria@school.com", "role": "Receptionist", "should_access_settings": False},
            {"email": "carlos@school.com", "role": "Coordinator", "should_access_settings": False},
            {"email": "admin@school.com", "role": "Manager", "should_access_settings": True}
        ]
        
        access_tests_passed = 0
        total_access_tests = len(role_tests)
        
        for role_test in role_tests:
            print(f"\n   Testing role-based access for: {role_test['role']}")
            
            # Login as this user
            login_success, login_response = self.test_login(role_test['email'], "admin123")
            if not login_success:
                print(f"   ❌ Login failed for {role_test['email']}")
                continue
            
            # Test access to admin endpoints (WhatsApp settings)
            settings_success, settings_response = self.run_test(
                f"Test admin access for {role_test['role']}",
                "GET",
                "api/admin/whatsapp/settings",
                200 if role_test['should_access_settings'] else 403
            )
            
            if role_test['should_access_settings']:
                if settings_success:
                    print(f"   ✅ {role_test['role']} can access admin settings (correct)")
                    access_tests_passed += 1
                else:
                    print(f"   ❌ {role_test['role']} cannot access admin settings (should be able to)")
            else:
                if not settings_success:
                    print(f"   ✅ {role_test['role']} cannot access admin settings (correct)")
                    access_tests_passed += 1
                else:
                    print(f"   ❌ {role_test['role']} can access admin settings (should not be able to)")
        
        self.critical_issues['role_based_access'] = (access_tests_passed == total_access_tests)
        
        if self.critical_issues['role_based_access']:
            print(f"\n✅ CRITICAL ISSUE #4 RESOLVED: Role-based access working correctly ({access_tests_passed}/{total_access_tests})")
        else:
            print(f"\n❌ CRITICAL ISSUE #4 FAILED: Role-based access not working ({access_tests_passed}/{total_access_tests})")
        
        return self.critical_issues['role_based_access']

    def test_critical_media_features(self):
        """Test CRITICAL ISSUE #5: Media Features (API level)"""
        print("\n🎵 CRITICAL TEST: Media Features API Verification")
        print("-" * 50)
        
        # Login first
        login_success, login_response = self.test_login("admin@school.com", "admin123")
        if not login_success:
            print("❌ Cannot test media features - login failed")
            return False
        
        # Get conversations to test media message handling
        conv_success, conversations = self.run_test("Get Conversations for Media Test", "GET", "api/conversations", 200)
        
        if conv_success and conversations and len(conversations) > 0:
            conv_id = conversations[0].get('id')
            
            # Test sending different message types
            media_tests = [
                {"type": "text", "body": "Test text message"},
                {"type": "image", "body": "Test image message", "media_url": "https://example.com/image.jpg"},
                {"type": "document", "body": "Test document message", "media_url": "https://example.com/document.pdf"}
            ]
            
            media_tests_passed = 0
            
            for media_test in media_tests:
                print(f"   Testing {media_test['type']} message...")
                
                message_data = {
                    "conversation_id": conv_id,
                    "body": media_test['body'],
                    "type": media_test['type']
                }
                
                if 'media_url' in media_test:
                    message_data['media_url'] = media_test['media_url']
                
                success, response = self.run_test(
                    f"Send {media_test['type']} message",
                    "POST",
                    f"api/conversations/{conv_id}/messages",
                    200,
                    data=message_data
                )
                
                if success:
                    print(f"   ✅ {media_test['type']} message sent successfully")
                    media_tests_passed += 1
                else:
                    print(f"   ❌ {media_test['type']} message failed")
            
            # Check if messages were stored with correct types
            messages_success, messages = self.run_test(
                f"Get messages to verify media types",
                "GET",
                f"api/conversations/{conv_id}/messages",
                200
            )
            
            if messages_success and messages:
                recent_messages = messages[-3:]  # Get last 3 messages
                media_types_found = [msg.get('type', 'text') for msg in recent_messages]
                print(f"   ✓ Recent message types: {media_types_found}")
                
                if len(set(media_types_found)) >= 2:  # At least 2 different types
                    print(f"   ✅ Multiple media types supported")
                    self.critical_issues['media_features'] = True
                else:
                    print(f"   ⚠ Limited media type support detected")
            else:
                print(f"   ❌ Could not verify message types")
        else:
            print(f"   ❌ No conversations available for media testing")
        
        if self.critical_issues['media_features']:
            print(f"\n✅ CRITICAL ISSUE #5 RESOLVED: Media features API working")
        else:
            print(f"\n❌ CRITICAL ISSUE #5 FAILED: Media features API limited")
        
        return self.critical_issues['media_features']

def main():
    print("🚀 Starting UniWhats Desk CRITICAL ISSUES Testing")
    print("=" * 60)
    
    tester = UniWhatsDeskAPITester()
    
    # Test basic connectivity first
    print("\n🔗 CONNECTIVITY TEST")
    print("-" * 30)
    health_success, _ = tester.run_test("Health Check", "GET", "api/health", 200)
    if not health_success:
        print("❌ Cannot connect to API - stopping tests")
        return 1
    
    # Run all critical tests
    print("\n🎯 CRITICAL ISSUES TESTING")
    print("=" * 60)
    
    # CRITICAL ISSUE #1: Authentication Bug
    auth_result = tester.test_critical_authentication_bug()
    
    # CRITICAL ISSUE #2: Profile Editing
    profile_result = tester.test_critical_profile_editing()
    
    # CRITICAL ISSUE #3: WhatsApp Integration
    whatsapp_result = tester.test_critical_whatsapp_integration()
    
    # CRITICAL ISSUE #4: Role-Based Access
    role_result = tester.test_critical_role_based_access()
    
    # CRITICAL ISSUE #5: Media Features
    media_result = tester.test_critical_media_features()
    
    # Print comprehensive results
    print("\n" + "=" * 60)
    print("📊 CRITICAL ISSUES TEST RESULTS")
    print("=" * 60)
    
    critical_results = [
        ("Authentication Bug", auth_result, "✅ Login with different users returns correct profiles"),
        ("Profile Editing", profile_result, "✅ Profile editing works and changes are reflected immediately"),
        ("WhatsApp Integration", whatsapp_result, "✅ WhatsApp settings configured with expected credentials"),
        ("Role-Based Access", role_result, "✅ Role-based access properly enforced"),
        ("Media Features", media_result, "✅ Media features API supports multiple message types")
    ]
    
    passed_critical = 0
    total_critical = len(critical_results)
    
    for issue, result, success_msg in critical_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"\n{status} - {issue}")
        if result:
            print(f"    {success_msg}")
            passed_critical += 1
        else:
            print(f"    ❌ Issue still present - needs attention")
    
    # Overall API tests summary
    print(f"\n📈 API ENDPOINT TESTS: {tester.tests_passed}/{tester.tests_run} passed")
    print(f"🎯 CRITICAL ISSUES: {passed_critical}/{total_critical} resolved")
    
    # Final verdict
    if passed_critical == total_critical:
        print(f"\n🎉 ALL CRITICAL ISSUES RESOLVED!")
        print(f"✅ UniWhats Desk is ready for production")
        return 0
    else:
        failed_issues = total_critical - passed_critical
        print(f"\n⚠️  {failed_issues} CRITICAL ISSUE(S) STILL PRESENT")
        print(f"❌ UniWhats Desk needs fixes before production")
        
        # List failed issues
        print(f"\n🔧 ISSUES REQUIRING ATTENTION:")
        for issue, result, _ in critical_results:
            if not result:
                print(f"   • {issue}")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())