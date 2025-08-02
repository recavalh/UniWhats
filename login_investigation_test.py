#!/usr/bin/env python3
"""
Login Investigation Test - Specific test for "Invalid credentials" issue
Testing all users mentioned in the review request:
- admin@school.com / admin123
- maria@school.com / maria123  
- carlos@school.com / carlos123
- ana@school.com / ana123
"""

import requests
import json
import sys
from datetime import datetime

class LoginInvestigationTester:
    def __init__(self, base_url="https://2f0940df-cae2-4a25-adec-94b80d9762a7.preview.emergentagent.com"):
        self.base_url = base_url
        self.test_results = []
        
    def log_result(self, test_name, success, details):
        """Log test result"""
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
    def test_single_login(self, email, password, expected_name=None):
        """Test login for a single user"""
        print(f"\n🔍 Testing login: {email} / {password}")
        print("-" * 50)
        
        url = f"{self.base_url}/api/auth/login"
        headers = {'Content-Type': 'application/json'}
        data = {"email": email, "password": password}
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    print(f"   ✅ LOGIN SUCCESS")
                    
                    # Check if token is present
                    if 'token' in response_data:
                        token = response_data['token']
                        print(f"   ✅ Token received: {token[:30]}...")
                    else:
                        print(f"   ❌ No token in response")
                        
                    # Check user data
                    if 'user' in response_data:
                        user = response_data['user']
                        actual_name = user.get('name', 'Unknown')
                        actual_role = user.get('role', 'Unknown')
                        actual_email = user.get('email', 'Unknown')
                        
                        print(f"   ✅ User data received:")
                        print(f"      Name: {actual_name}")
                        print(f"      Role: {actual_role}")
                        print(f"      Email: {actual_email}")
                        
                        # Verify expected name if provided
                        if expected_name and actual_name != expected_name:
                            print(f"   ⚠️  Expected name: {expected_name}, got: {actual_name}")
                            
                        self.log_result(f"Login {email}", True, {
                            'user': user,
                            'token_present': 'token' in response_data
                        })
                        return True, response_data
                    else:
                        print(f"   ❌ No user data in response")
                        self.log_result(f"Login {email}", False, "No user data in response")
                        return False, response_data
                        
                except json.JSONDecodeError:
                    print(f"   ❌ Invalid JSON response: {response.text}")
                    self.log_result(f"Login {email}", False, f"Invalid JSON: {response.text}")
                    return False, {}
                    
            elif response.status_code == 401:
                print(f"   ❌ LOGIN FAILED - Invalid credentials")
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', 'Unknown error')
                    print(f"   Error: {error_detail}")
                    self.log_result(f"Login {email}", False, f"401 - {error_detail}")
                except:
                    print(f"   Error response: {response.text}")
                    self.log_result(f"Login {email}", False, f"401 - {response.text}")
                return False, {}
                
            else:
                print(f"   ❌ Unexpected status code: {response.status_code}")
                print(f"   Response: {response.text}")
                self.log_result(f"Login {email}", False, f"Status {response.status_code}: {response.text}")
                return False, {}
                
        except requests.exceptions.Timeout:
            print(f"   ❌ Request timeout")
            self.log_result(f"Login {email}", False, "Request timeout")
            return False, {}
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection error")
            self.log_result(f"Login {email}", False, "Connection error")
            return False, {}
        except Exception as e:
            print(f"   ❌ Unexpected error: {str(e)}")
            self.log_result(f"Login {email}", False, f"Exception: {str(e)}")
            return False, {}
    
    def test_database_users(self):
        """Test if we can verify users exist in database by trying to login as admin first"""
        print(f"\n🗄️  Testing database connectivity and user verification")
        print("=" * 60)
        
        # First try to login as admin to get access to user list
        admin_success, admin_response = self.test_single_login("admin@school.com", "admin123", "João Diretor")
        
        if admin_success and 'token' in admin_response:
            token = admin_response['token']
            
            # Try to get users list to verify database content
            print(f"\n   Attempting to fetch users list...")
            url = f"{self.base_url}/api/admin/users"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    users = response.json()
                    print(f"   ✅ Found {len(users)} users in database:")
                    
                    expected_emails = ["admin@school.com", "maria@school.com", "carlos@school.com", "ana@school.com"]
                    found_emails = []
                    
                    for user in users:
                        email = user.get('email', 'Unknown')
                        name = user.get('name', 'Unknown')
                        role = user.get('role', 'Unknown')
                        user_id = user.get('id', 'Unknown')
                        
                        print(f"      • {email} - {name} ({role}) [ID: {user_id}]")
                        found_emails.append(email)
                    
                    # Check if all expected users are present
                    missing_users = [email for email in expected_emails if email not in found_emails]
                    if missing_users:
                        print(f"   ❌ Missing users: {missing_users}")
                        return False
                    else:
                        print(f"   ✅ All expected users found in database")
                        return True
                        
                else:
                    print(f"   ❌ Failed to get users list: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Error fetching users: {str(e)}")
                return False
        else:
            print(f"   ❌ Cannot verify database - admin login failed")
            return False
    
    def test_password_hashing(self):
        """Test if password hashing is working correctly by testing wrong passwords"""
        print(f"\n🔐 Testing password hashing and validation")
        print("=" * 60)
        
        # Test with wrong passwords - these should fail
        wrong_password_tests = [
            ("admin@school.com", "wrongpassword"),
            ("maria@school.com", "wrongpassword"),
            ("admin@school.com", ""),  # Empty password
            ("admin@school.com", "admin124"),  # Close but wrong
        ]
        
        failed_as_expected = 0
        
        for email, wrong_password in wrong_password_tests:
            print(f"\n   Testing WRONG password: {email} / {wrong_password}")
            success, _ = self.test_single_login(email, wrong_password)
            
            if not success:
                print(f"   ✅ Correctly rejected wrong password")
                failed_as_expected += 1
            else:
                print(f"   ❌ SECURITY ISSUE: Wrong password was accepted!")
        
        print(f"\n   Password validation results: {failed_as_expected}/{len(wrong_password_tests)} correctly rejected")
        return failed_as_expected == len(wrong_password_tests)
    
    def run_comprehensive_login_test(self):
        """Run comprehensive login investigation"""
        print("🔍 COMPREHENSIVE LOGIN INVESTIGATION")
        print("=" * 60)
        print("Testing all users mentioned in review request:")
        print("- admin@school.com / admin123")
        print("- maria@school.com / maria123")
        print("- carlos@school.com / carlos123") 
        print("- ana@school.com / ana123")
        print("=" * 60)
        
        # Test users as specified in review request
        test_users = [
            {"email": "admin@school.com", "password": "admin123", "expected_name": "João Diretor"},
            {"email": "maria@school.com", "password": "maria123", "expected_name": "Maria Silva"},
            {"email": "carlos@school.com", "password": "carlos123", "expected_name": "Carlos Souza"},
            {"email": "ana@school.com", "password": "ana123", "expected_name": "Ana Costa"}
        ]
        
        successful_logins = 0
        failed_logins = []
        
        for user_test in test_users:
            success, response = self.test_single_login(
                user_test["email"], 
                user_test["password"], 
                user_test["expected_name"]
            )
            
            if success:
                successful_logins += 1
            else:
                failed_logins.append({
                    'email': user_test["email"],
                    'password': user_test["password"],
                    'expected_name': user_test["expected_name"]
                })
        
        # Test database connectivity
        db_test_success = self.test_database_users()
        
        # Test password hashing
        password_test_success = self.test_password_hashing()
        
        # Print comprehensive results
        print(f"\n" + "=" * 60)
        print("📊 LOGIN INVESTIGATION RESULTS")
        print("=" * 60)
        
        print(f"\n✅ Successful logins: {successful_logins}/{len(test_users)}")
        
        if failed_logins:
            print(f"\n❌ Failed logins:")
            for failed in failed_logins:
                print(f"   • {failed['email']} / {failed['password']} (expected: {failed['expected_name']})")
        
        print(f"\n🗄️  Database verification: {'✅ PASS' if db_test_success else '❌ FAIL'}")
        print(f"🔐 Password hashing: {'✅ PASS' if password_test_success else '❌ FAIL'}")
        
        # Overall assessment
        if successful_logins == len(test_users) and db_test_success and password_test_success:
            print(f"\n🎉 ALL LOGIN TESTS PASSED")
            print(f"✅ No 'Invalid credentials' issue detected")
            print(f"✅ All users can login successfully")
            print(f"✅ Database contains expected users")
            print(f"✅ Password hashing working correctly")
            return True
        else:
            print(f"\n⚠️  LOGIN ISSUES DETECTED")
            
            if successful_logins < len(test_users):
                print(f"❌ {len(test_users) - successful_logins} users cannot login")
                
            if not db_test_success:
                print(f"❌ Database verification failed")
                
            if not password_test_success:
                print(f"❌ Password hashing issues detected")
                
            print(f"\n🔧 RECOMMENDED ACTIONS:")
            if failed_logins:
                print(f"   1. Check if failed users exist in database")
                print(f"   2. Verify password hashes for failed users")
                print(f"   3. Check if mock data initialization completed")
                
            return False

def main():
    print("🚀 Starting Login Investigation Test")
    print("Investigating 'Invalid credentials' issue reported by user")
    print("=" * 60)
    
    tester = LoginInvestigationTester()
    
    # Test basic connectivity first
    print(f"\n🔗 Testing API connectivity...")
    try:
        response = requests.get(f"{tester.base_url}/", timeout=10)
        if response.status_code == 200:
            print(f"✅ API is accessible")
        else:
            print(f"⚠️  API returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to API: {str(e)}")
        return 1
    
    # Run comprehensive login test
    success = tester.run_comprehensive_login_test()
    
    # Print detailed test log
    print(f"\n📋 DETAILED TEST LOG:")
    print("-" * 30)
    for result in tester.test_results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['test']} - {result['details']}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())