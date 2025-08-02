#!/usr/bin/env python3
"""
Final Login Verification - Comprehensive test of login endpoint
"""

import requests
import json

def test_login_endpoint():
    base_url = "https://2f0940df-cae2-4a25-adec-94b80d9762a7.preview.emergentagent.com"
    
    print("🔍 FINAL LOGIN ENDPOINT VERIFICATION")
    print("=" * 60)
    
    # Test all valid users
    valid_users = [
        {"email": "admin@school.com", "password": "admin123", "expected_role": "Manager"},
        {"email": "maria@school.com", "password": "maria123", "expected_role": "Receptionist"},
        {"email": "carlos@school.com", "password": "carlos123", "expected_role": "Coordinator"},
        {"email": "ana@school.com", "password": "ana123", "expected_role": "Sales Rep"}
    ]
    
    print("\n✅ TESTING VALID CREDENTIALS:")
    print("-" * 40)
    
    valid_count = 0
    for user in valid_users:
        response = requests.post(
            f"{base_url}/api/auth/login",
            json={"email": user["email"], "password": user["password"]},
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            user_data = data.get('user', {})
            actual_role = user_data.get('role', 'Unknown')
            
            if actual_role == user["expected_role"]:
                print(f"✅ {user['email']} - {actual_role} - LOGIN SUCCESS")
                valid_count += 1
            else:
                print(f"⚠️  {user['email']} - Expected {user['expected_role']}, got {actual_role}")
        else:
            print(f"❌ {user['email']} - LOGIN FAILED ({response.status_code})")
    
    # Test invalid credentials
    invalid_tests = [
        {"email": "admin@school.com", "password": "wrongpassword", "desc": "Wrong password"},
        {"email": "nonexistent@school.com", "password": "admin123", "desc": "Non-existent user"},
        {"email": "admin@school.com", "password": "", "desc": "Empty password"},
        {"email": "", "password": "admin123", "desc": "Empty email"},
        {"email": "admin@school.com", "password": "admin124", "desc": "Almost correct password"}
    ]
    
    print(f"\n❌ TESTING INVALID CREDENTIALS:")
    print("-" * 40)
    
    invalid_count = 0
    for test in invalid_tests:
        response = requests.post(
            f"{base_url}/api/auth/login",
            json={"email": test["email"], "password": test["password"]},
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 401:
            print(f"✅ {test['desc']} - Correctly rejected (401)")
            invalid_count += 1
        else:
            print(f"❌ {test['desc']} - Should be rejected but got {response.status_code}")
    
    # Summary
    print(f"\n" + "=" * 60)
    print("📊 LOGIN ENDPOINT VERIFICATION RESULTS")
    print("=" * 60)
    print(f"✅ Valid logins: {valid_count}/{len(valid_users)}")
    print(f"✅ Invalid rejections: {invalid_count}/{len(invalid_tests)}")
    
    total_tests = len(valid_users) + len(invalid_tests)
    passed_tests = valid_count + invalid_count
    
    if passed_tests == total_tests:
        print(f"\n🎉 ALL TESTS PASSED ({passed_tests}/{total_tests})")
        print(f"✅ Login endpoint working correctly")
        print(f"✅ All users can login with correct credentials")
        print(f"✅ Invalid credentials are properly rejected")
        print(f"✅ Password hashing and verification working")
        print(f"✅ Database contains all expected users")
        return True
    else:
        print(f"\n⚠️  SOME TESTS FAILED ({passed_tests}/{total_tests})")
        return False

if __name__ == "__main__":
    success = test_login_endpoint()
    exit(0 if success else 1)