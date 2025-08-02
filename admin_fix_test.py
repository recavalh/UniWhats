#!/usr/bin/env python3
"""
Admin Fix Test - Test login with the updated admin email
"""

import requests
import json

def test_updated_admin():
    base_url = "https://2f0940df-cae2-4a25-adec-94b80d9762a7.preview.emergentagent.com"
    
    print("🔍 TESTING UPDATED ADMIN EMAIL")
    print("=" * 50)
    
    # Try to login with the updated email found in database
    updated_email = "admin.updated.214328@school.com"
    password = "admin123"
    
    print(f"Testing login: {updated_email} / {password}")
    
    response = requests.post(
        f"{base_url}/api/auth/login",
        json={"email": updated_email, "password": password},
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        user = data.get('user', {})
        
        print("✅ LOGIN SUCCESSFUL!")
        print(f"   Name: {user.get('name', 'Unknown')}")
        print(f"   Role: {user.get('role', 'Unknown')}")
        print(f"   Email: {user.get('email', 'Unknown')}")
        print(f"   Token: {data.get('token', 'No token')[:30]}...")
        
        # Now let's try to get the users list to confirm admin access
        token = data.get('token')
        if token:
            print(f"\nTesting admin access with updated email...")
            users_response = requests.get(
                f"{base_url}/api/admin/users",
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token}'
                }
            )
            
            if users_response.status_code == 200:
                users = users_response.json()
                print(f"✅ Admin access confirmed - found {len(users)} users:")
                for user in users:
                    print(f"   • {user.get('email', 'Unknown')} - {user.get('name', 'Unknown')} ({user.get('role', 'Unknown')})")
                return True
            else:
                print(f"❌ Admin access denied: {users_response.status_code}")
                return False
        
    else:
        print(f"❌ LOGIN FAILED")
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    success = test_updated_admin()
    
    if success:
        print(f"\n✅ ADMIN LOGIN ISSUE IDENTIFIED AND CONFIRMED")
        print(f"🔧 ROOT CAUSE: Admin email was changed during profile editing tests")
        print(f"📧 Original email: admin@school.com")
        print(f"📧 Current email: admin.updated.214328@school.com")
        print(f"🔑 Password: admin123 (still works)")
        print(f"\n💡 SOLUTION: Either:")
        print(f"   1. Use the updated email for admin login")
        print(f"   2. Reset admin email back to admin@school.com")
        print(f"   3. Create a new admin user with admin@school.com")
    else:
        print(f"\n❌ ADMIN LOGIN STILL NOT WORKING")