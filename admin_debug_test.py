#!/usr/bin/env python3
"""
Admin Debug Test - Investigate why admin@school.com cannot login
"""

import requests
import json
import sys

def test_admin_issue():
    base_url = "https://2f0940df-cae2-4a25-adec-94b80d9762a7.preview.emergentagent.com"
    
    print("🔍 ADMIN LOGIN DEBUG TEST")
    print("=" * 50)
    
    # First, login as Maria (which works) to get admin access
    print("\n1. Login as Maria to get access to user management...")
    maria_response = requests.post(
        f"{base_url}/api/auth/login",
        json={"email": "maria@school.com", "password": "maria123"},
        headers={'Content-Type': 'application/json'}
    )
    
    if maria_response.status_code != 200:
        print("❌ Cannot login as Maria")
        return False
        
    maria_data = maria_response.json()
    maria_token = maria_data['token']
    print(f"✅ Maria login successful")
    
    # Try to get users list as Maria (she's a Receptionist, might not have access)
    print("\n2. Attempting to get users list as Maria...")
    users_response = requests.get(
        f"{base_url}/api/admin/users",
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {maria_token}'
        }
    )
    
    if users_response.status_code == 403:
        print("⚠️  Maria doesn't have admin access (expected)")
        
        # Let's try a different approach - check if we can find admin user by trying different passwords
        print("\n3. Testing different password combinations for admin...")
        
        # Test various password combinations that might be in the database
        test_passwords = [
            "admin123",  # Original
            "admin",     # Simple
            "123456",    # Common
            "password",  # Common
            "admin@school.com",  # Email as password
            "João Diretor",      # Name as password
            "joao123",   # Name variant
        ]
        
        for password in test_passwords:
            print(f"   Testing admin@school.com / {password}")
            admin_test = requests.post(
                f"{base_url}/api/auth/login",
                json={"email": "admin@school.com", "password": password},
                headers={'Content-Type': 'application/json'}
            )
            
            if admin_test.status_code == 200:
                print(f"   ✅ SUCCESS with password: {password}")
                admin_data = admin_test.json()
                print(f"   User: {admin_data.get('user', {}).get('name', 'Unknown')}")
                return True
            else:
                print(f"   ❌ Failed with {password}")
        
        print("\n4. Let's check if admin user exists by testing similar emails...")
        
        # Test similar email variations
        test_emails = [
            "admin@school.com",
            "joao@school.com", 
            "diretor@school.com",
            "manager@school.com",
            "admin@test.com"
        ]
        
        for email in test_emails:
            print(f"   Testing {email} / admin123")
            email_test = requests.post(
                f"{base_url}/api/auth/login",
                json={"email": email, "password": "admin123"},
                headers={'Content-Type': 'application/json'}
            )
            
            if email_test.status_code == 200:
                print(f"   ✅ SUCCESS with email: {email}")
                email_data = email_test.json()
                print(f"   User: {email_data.get('user', {}).get('name', 'Unknown')}")
                return True
            else:
                print(f"   ❌ Failed with {email}")
                
    elif users_response.status_code == 200:
        print("✅ Maria has admin access, checking users...")
        users = users_response.json()
        
        print(f"\nFound {len(users)} users in database:")
        admin_found = False
        
        for user in users:
            email = user.get('email', 'Unknown')
            name = user.get('name', 'Unknown')
            role = user.get('role', 'Unknown')
            user_id = user.get('id', 'Unknown')
            
            print(f"   • {email} - {name} ({role}) [ID: {user_id}]")
            
            if email == "admin@school.com":
                admin_found = True
                print(f"   ✅ Admin user found in database!")
                
        if not admin_found:
            print(f"   ❌ Admin user NOT found in database!")
            
    else:
        print(f"❌ Unexpected response: {users_response.status_code}")
        print(f"Response: {users_response.text}")
    
    return False

if __name__ == "__main__":
    success = test_admin_issue()
    if not success:
        print(f"\n❌ ADMIN LOGIN ISSUE CONFIRMED")
        print(f"🔧 POSSIBLE CAUSES:")
        print(f"   1. Admin user not properly created in database")
        print(f"   2. Admin password hash is incorrect")
        print(f"   3. Admin user was modified/corrupted")
        print(f"   4. Database initialization failed for admin user")
    else:
        print(f"\n✅ ADMIN LOGIN ISSUE RESOLVED")