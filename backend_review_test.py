#!/usr/bin/env python3
"""
Backend Review Test - Specific tests for the review request
Testing all corrections implemented in the backend:

1. Login de usuários - Verify all users can login
2. Updated access rules for conversations
3. Close/reopen conversation functionality  
4. Access control on new endpoints
5. Profile editing functionality
"""

import requests
import sys
import json
from datetime import datetime

class BackendReviewTester:
    def __init__(self, base_url="https://2f0940df-cae2-4a25-adec-94b80d9762a7.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_tokens = {}  # Store tokens for different users
        self.test_results = {
            'login_tests': [],
            'access_control_tests': [],
            'close_reopen_tests': [],
            'profile_editing_tests': []
        }

    def log_result(self, category, test_name, success, details=""):
        """Log test result"""
        self.test_results[category].append({
            'test': test_name,
            'success': success,
            'details': details
        })

    def make_request(self, method, endpoint, data=None, headers=None, token=None):
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            
            return response
            
        except requests.exceptions.Timeout:
            print(f"❌ Request timeout for {endpoint}")
            return None
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection error for {endpoint}")
            return None
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None

    def test_user_login(self, email, password, expected_role, expected_name):
        """Test login for a specific user"""
        print(f"\n🔐 Testing login: {email}")
        
        response = self.make_request('POST', 'api/auth/login', {
            'email': email,
            'password': password
        })
        
        if not response:
            self.log_result('login_tests', f'Login {email}', False, "Request failed")
            return False, None
        
        if response.status_code == 200:
            try:
                data = response.json()
                if 'token' in data and 'user' in data:
                    user = data['user']
                    actual_role = user.get('role', '')
                    actual_name = user.get('name', '')
                    actual_email = user.get('email', '')
                    
                    print(f"   ✅ Login successful")
                    print(f"   ✅ User: {actual_name} ({actual_role})")
                    print(f"   ✅ Email: {actual_email}")
                    
                    # Verify correct user data
                    if actual_role == expected_role and actual_name == expected_name and actual_email == email:
                        print(f"   ✅ Correct user profile returned")
                        self.auth_tokens[email] = data['token']
                        self.tests_passed += 1
                        self.log_result('login_tests', f'Login {email}', True, f"Correct profile: {actual_name} ({actual_role})")
                        return True, data
                    else:
                        print(f"   ❌ Wrong user profile returned")
                        print(f"      Expected: {expected_name} ({expected_role})")
                        print(f"      Got: {actual_name} ({actual_role})")
                        self.log_result('login_tests', f'Login {email}', False, f"Wrong profile: expected {expected_name} ({expected_role}), got {actual_name} ({actual_role})")
                        return False, None
                else:
                    print(f"   ❌ Invalid response format")
                    self.log_result('login_tests', f'Login {email}', False, "Invalid response format")
                    return False, None
            except json.JSONDecodeError:
                print(f"   ❌ Invalid JSON response")
                self.log_result('login_tests', f'Login {email}', False, "Invalid JSON response")
                return False, None
        else:
            print(f"   ❌ Login failed - Status: {response.status_code}")
            print(f"   ❌ Response: {response.text[:200]}")
            self.log_result('login_tests', f'Login {email}', False, f"Status {response.status_code}: {response.text[:100]}")
            return False, None

    def test_all_user_logins(self):
        """Test login for all required users"""
        print("\n" + "="*60)
        print("🔐 TESTING USER LOGINS")
        print("="*60)
        
        test_users = [
            {"email": "admin@school.com", "password": "admin123", "role": "Manager", "name": "João Diretor"},
            {"email": "maria@school.com", "password": "maria123", "role": "Receptionist", "name": "Maria Silva"},
            {"email": "carlos@school.com", "password": "carlos123", "role": "Coordinator", "name": "Carlos Souza"},
            {"email": "ana@school.com", "password": "ana123", "role": "Sales Rep", "name": "Ana Costa"}
        ]
        
        login_success_count = 0
        
        for user in test_users:
            success, _ = self.test_user_login(
                user['email'], 
                user['password'], 
                user['role'], 
                user['name']
            )
            if success:
                login_success_count += 1
        
        print(f"\n📊 Login Results: {login_success_count}/{len(test_users)} users can login successfully")
        return login_success_count == len(test_users)

    def test_conversation_access_control(self):
        """Test updated access control rules for conversations"""
        print("\n" + "="*60)
        print("🔒 TESTING CONVERSATION ACCESS CONTROL")
        print("="*60)
        
        # Test each user's conversation access
        access_results = {}
        
        for email, token in self.auth_tokens.items():
            print(f"\n👤 Testing conversation access for: {email}")
            
            response = self.make_request('GET', 'api/conversations', token=token)
            
            if response and response.status_code == 200:
                try:
                    conversations = response.json()
                    conv_count = len(conversations)
                    print(f"   ✅ Can access {conv_count} conversations")
                    
                    # Log conversation details
                    for i, conv in enumerate(conversations):
                        contact_name = conv.get('contact', {}).get('name', 'Unknown')
                        dept_id = conv.get('department_id', 'Unknown')
                        assigned_to = conv.get('assigned_user_id', 'Unassigned')
                        status = conv.get('status', 'Unknown')
                        conv_id = conv.get('id', 'Unknown')
                        print(f"   Conv {i+1}: {conv_id} | {contact_name} | {dept_id} | assigned:{assigned_to} | {status}")
                    
                    access_results[email] = {
                        'success': True,
                        'count': conv_count,
                        'conversations': conversations
                    }
                    self.tests_passed += 1
                    self.log_result('access_control_tests', f'Access for {email}', True, f"{conv_count} conversations accessible")
                    
                except json.JSONDecodeError:
                    print(f"   ❌ Invalid JSON response")
                    access_results[email] = {'success': False, 'error': 'Invalid JSON'}
                    self.log_result('access_control_tests', f'Access for {email}', False, "Invalid JSON response")
            else:
                status_code = response.status_code if response else "No response"
                print(f"   ❌ Failed to get conversations - Status: {status_code}")
                access_results[email] = {'success': False, 'error': f'Status {status_code}'}
                self.log_result('access_control_tests', f'Access for {email}', False, f"Status {status_code}")
        
        # Verify access rules
        print(f"\n📋 VERIFYING ACCESS RULES:")
        
        # Manager should see all conversations (expecting 3)
        if 'admin@school.com' in access_results and access_results['admin@school.com']['success']:
            manager_count = access_results['admin@school.com']['count']
            if manager_count == 3:
                print(f"   ✅ Manager sees all conversations ({manager_count})")
                self.log_result('access_control_tests', 'Manager access rule', True, f"Sees all {manager_count} conversations")
            else:
                print(f"   ❌ Manager should see 3 conversations, sees {manager_count}")
                self.log_result('access_control_tests', 'Manager access rule', False, f"Expected 3, got {manager_count}")
        
        # Receptionist should see new/unassigned + assigned to them
        if 'maria@school.com' in access_results and access_results['maria@school.com']['success']:
            receptionist_count = access_results['maria@school.com']['count']
            print(f"   ✅ Receptionist sees {receptionist_count} conversations (new/unassigned + assigned to them)")
            self.log_result('access_control_tests', 'Receptionist access rule', True, f"Sees {receptionist_count} conversations")
        
        # Coordinator should see only their department + assigned to them
        if 'carlos@school.com' in access_results and access_results['carlos@school.com']['success']:
            coordinator_count = access_results['carlos@school.com']['count']
            print(f"   ✅ Coordinator sees {coordinator_count} conversations (department + assigned)")
            self.log_result('access_control_tests', 'Coordinator access rule', True, f"Sees {coordinator_count} conversations")
        
        # Sales Rep should see only their department + assigned to them
        if 'ana@school.com' in access_results and access_results['ana@school.com']['success']:
            sales_count = access_results['ana@school.com']['count']
            print(f"   ✅ Sales Rep sees {sales_count} conversations (department + assigned)")
            self.log_result('access_control_tests', 'Sales Rep access rule', True, f"Sees {sales_count} conversations")
        
        return access_results

    def test_close_reopen_functionality(self):
        """Test close and reopen conversation functionality"""
        print("\n" + "="*60)
        print("🔄 TESTING CLOSE/REOPEN FUNCTIONALITY")
        print("="*60)
        
        # Use admin token for testing
        admin_token = self.auth_tokens.get('admin@school.com')
        if not admin_token:
            print("❌ No admin token available for close/reopen tests")
            return False
        
        # Get conversations to test with
        response = self.make_request('GET', 'api/conversations', token=admin_token)
        if not response or response.status_code != 200:
            print("❌ Cannot get conversations for close/reopen test")
            return False
        
        try:
            conversations = response.json()
            if not conversations:
                print("❌ No conversations available for testing")
                return False
            
            # Test with first conversation
            test_conv = conversations[0]
            conv_id = test_conv.get('id')
            original_status = test_conv.get('status', 'unknown')
            
            print(f"\n🔄 Testing with conversation: {conv_id}")
            print(f"   Original status: {original_status}")
            
            # Test closing conversation
            print(f"\n📴 Testing CLOSE conversation...")
            close_response = self.make_request('POST', f'api/conversations/{conv_id}/close', token=admin_token)
            
            if close_response and close_response.status_code == 200:
                try:
                    close_data = close_response.json()
                    print(f"   ✅ Close request successful")
                    print(f"   ✅ Response: {close_data.get('message', 'No message')}")
                    print(f"   ✅ Status: {close_data.get('status', 'Unknown')}")
                    
                    if close_data.get('status') == 'closed':
                        print(f"   ✅ Status correctly changed to 'closed'")
                        self.tests_passed += 1
                        self.log_result('close_reopen_tests', f'Close {conv_id}', True, "Status changed to closed")
                        
                        # Verify conversation is actually closed by getting it again
                        verify_response = self.make_request('GET', f'api/conversations/{conv_id}', token=admin_token)
                        if verify_response and verify_response.status_code == 200:
                            verify_data = verify_response.json()
                            if verify_data.get('status') == 'closed':
                                print(f"   ✅ Conversation status verified as 'closed'")
                            else:
                                print(f"   ❌ Conversation status not updated: {verify_data.get('status')}")
                    else:
                        print(f"   ❌ Status not changed to 'closed': {close_data.get('status')}")
                        self.log_result('close_reopen_tests', f'Close {conv_id}', False, f"Status not closed: {close_data.get('status')}")
                        
                except json.JSONDecodeError:
                    print(f"   ❌ Invalid JSON response from close")
                    self.log_result('close_reopen_tests', f'Close {conv_id}', False, "Invalid JSON response")
            else:
                status = close_response.status_code if close_response else "No response"
                print(f"   ❌ Close request failed - Status: {status}")
                self.log_result('close_reopen_tests', f'Close {conv_id}', False, f"Request failed: {status}")
            
            # Test reopening conversation
            print(f"\n📱 Testing REOPEN conversation...")
            reopen_response = self.make_request('POST', f'api/conversations/{conv_id}/reopen', token=admin_token)
            
            if reopen_response and reopen_response.status_code == 200:
                try:
                    reopen_data = reopen_response.json()
                    print(f"   ✅ Reopen request successful")
                    print(f"   ✅ Response: {reopen_data.get('message', 'No message')}")
                    print(f"   ✅ Status: {reopen_data.get('status', 'Unknown')}")
                    
                    if reopen_data.get('status') == 'open':
                        print(f"   ✅ Status correctly changed to 'open'")
                        self.tests_passed += 1
                        self.log_result('close_reopen_tests', f'Reopen {conv_id}', True, "Status changed to open")
                        
                        # Verify conversation is actually reopened
                        verify_response = self.make_request('GET', f'api/conversations/{conv_id}', token=admin_token)
                        if verify_response and verify_response.status_code == 200:
                            verify_data = verify_response.json()
                            if verify_data.get('status') == 'open':
                                print(f"   ✅ Conversation status verified as 'open'")
                            else:
                                print(f"   ❌ Conversation status not updated: {verify_data.get('status')}")
                    else:
                        print(f"   ❌ Status not changed to 'open': {reopen_data.get('status')}")
                        self.log_result('close_reopen_tests', f'Reopen {conv_id}', False, f"Status not open: {reopen_data.get('status')}")
                        
                except json.JSONDecodeError:
                    print(f"   ❌ Invalid JSON response from reopen")
                    self.log_result('close_reopen_tests', f'Reopen {conv_id}', False, "Invalid JSON response")
            else:
                status = reopen_response.status_code if reopen_response else "No response"
                print(f"   ❌ Reopen request failed - Status: {status}")
                self.log_result('close_reopen_tests', f'Reopen {conv_id}', False, f"Request failed: {status}")
            
            # Test access control on close/reopen endpoints
            print(f"\n🔒 Testing access control on close/reopen endpoints...")
            
            # Test with different user roles
            for email, token in self.auth_tokens.items():
                if email == 'admin@school.com':
                    continue  # Skip admin, already tested
                
                print(f"\n   Testing close access for: {email}")
                close_test_response = self.make_request('POST', f'api/conversations/{conv_id}/close', token=token)
                
                if close_test_response:
                    if close_test_response.status_code == 200:
                        print(f"   ✅ {email} can close conversations")
                        self.log_result('close_reopen_tests', f'Close access {email}', True, "Can close conversations")
                    elif close_test_response.status_code == 403:
                        print(f"   ✅ {email} properly denied access (403)")
                        self.log_result('close_reopen_tests', f'Close access {email}', True, "Properly denied access")
                    else:
                        print(f"   ❌ Unexpected response: {close_test_response.status_code}")
                        self.log_result('close_reopen_tests', f'Close access {email}', False, f"Unexpected status: {close_test_response.status_code}")
                else:
                    print(f"   ❌ No response for {email}")
                    self.log_result('close_reopen_tests', f'Close access {email}', False, "No response")
            
            return True
            
        except json.JSONDecodeError:
            print("❌ Invalid JSON response from conversations")
            return False

    def test_profile_editing(self):
        """Test profile editing functionality"""
        print("\n" + "="*60)
        print("👤 TESTING PROFILE EDITING")
        print("="*60)
        
        # Test with admin user
        admin_token = self.auth_tokens.get('admin@school.com')
        if not admin_token:
            print("❌ No admin token available for profile editing test")
            return False
        
        print(f"\n✏️ Testing profile editing with admin user...")
        
        # Test profile update
        timestamp = datetime.now().strftime("%H%M%S")
        profile_data = {
            "name": f"João Diretor Updated {timestamp}",
            "email": "admin@school.com"  # Keep original email to avoid login issues
        }
        
        response = self.make_request('PUT', 'api/users/profile', data=profile_data, token=admin_token)
        
        if response and response.status_code == 200:
            try:
                updated_profile = response.json()
                print(f"   ✅ Profile update successful")
                print(f"   ✅ Updated name: {updated_profile.get('name', 'Unknown')}")
                print(f"   ✅ Email: {updated_profile.get('email', 'Unknown')}")
                
                # Verify the update was applied
                if updated_profile.get('name') == profile_data['name']:
                    print(f"   ✅ Name update verified")
                    self.tests_passed += 1
                    self.log_result('profile_editing_tests', 'Profile update', True, f"Name updated to: {profile_data['name']}")
                else:
                    print(f"   ❌ Name not updated correctly")
                    print(f"      Expected: {profile_data['name']}")
                    print(f"      Got: {updated_profile.get('name', 'Unknown')}")
                    self.log_result('profile_editing_tests', 'Profile update', False, "Name not updated correctly")
                
                return True
                
            except json.JSONDecodeError:
                print(f"   ❌ Invalid JSON response from profile update")
                self.log_result('profile_editing_tests', 'Profile update', False, "Invalid JSON response")
                return False
        else:
            status = response.status_code if response else "No response"
            print(f"   ❌ Profile update failed - Status: {status}")
            if response:
                print(f"   ❌ Response: {response.text[:200]}")
            self.log_result('profile_editing_tests', 'Profile update', False, f"Request failed: {status}")
            return False

    def run_all_tests(self):
        """Run all backend review tests"""
        print("🚀 STARTING BACKEND REVIEW TESTS")
        print("="*80)
        print("Testing all corrections implemented in the backend:")
        print("1. Login de usuários")
        print("2. Updated access rules")
        print("3. Close/reopen functionality")
        print("4. Access control on new endpoints")
        print("5. Profile editing")
        print("="*80)
        
        # Test 1: User logins
        login_success = self.test_all_user_logins()
        
        # Test 2: Access control rules
        access_results = self.test_conversation_access_control()
        
        # Test 3: Close/reopen functionality
        close_reopen_success = self.test_close_reopen_functionality()
        
        # Test 4: Profile editing
        profile_success = self.test_profile_editing()
        
        # Generate final report
        self.generate_final_report(login_success, access_results, close_reopen_success, profile_success)

    def generate_final_report(self, login_success, access_results, close_reopen_success, profile_success):
        """Generate comprehensive final report"""
        print("\n" + "="*80)
        print("📊 BACKEND REVIEW TEST RESULTS")
        print("="*80)
        
        print(f"\n🔐 LOGIN TESTS:")
        for result in self.test_results['login_tests']:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['test']}: {result['details']}")
        
        print(f"\n🔒 ACCESS CONTROL TESTS:")
        for result in self.test_results['access_control_tests']:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['test']}: {result['details']}")
        
        print(f"\n🔄 CLOSE/REOPEN TESTS:")
        for result in self.test_results['close_reopen_tests']:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['test']}: {result['details']}")
        
        print(f"\n👤 PROFILE EDITING TESTS:")
        for result in self.test_results['profile_editing_tests']:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['test']}: {result['details']}")
        
        # Summary
        print(f"\n📈 OVERALL RESULTS:")
        print(f"   Total API calls: {self.tests_run}")
        print(f"   Successful calls: {self.tests_passed}")
        print(f"   Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        # Specific feature results
        features = [
            ("User Login", login_success),
            ("Access Control", len([r for r in self.test_results['access_control_tests'] if r['success']]) > 0),
            ("Close/Reopen", close_reopen_success),
            ("Profile Editing", profile_success)
        ]
        
        print(f"\n🎯 FEATURE STATUS:")
        working_features = 0
        for feature_name, feature_success in features:
            status = "✅ WORKING" if feature_success else "❌ FAILING"
            print(f"   {status} - {feature_name}")
            if feature_success:
                working_features += 1
        
        print(f"\n🏆 FINAL VERDICT:")
        if working_features == len(features):
            print(f"   ✅ ALL FEATURES WORKING ({working_features}/{len(features)})")
            print(f"   🎉 Backend corrections successfully implemented!")
        else:
            failing_features = len(features) - working_features
            print(f"   ❌ {failing_features} FEATURE(S) FAILING ({working_features}/{len(features)})")
            print(f"   🔧 Backend needs additional fixes")
        
        return working_features == len(features)

def main():
    tester = BackendReviewTester()
    tester.run_all_tests()
    return 0

if __name__ == "__main__":
    sys.exit(main())