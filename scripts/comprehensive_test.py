#!/usr/bin/env python
"""
Comprehensive test script for NashLibrary authentication system.
Tests all authentication flows and verifies database/code alignment.
"""

import sys
from backend.app import app

def test_admin_login():
    """Test admin login"""
    print("\n=== TEST 1: Admin Login ===")
    with app.test_client() as client:
        response = client.post('/login', 
            json={'email': 'admin@library.com', 'password': 'admin123', 'role': 'admin'}
        )
        if response.status_code == 200:
            data = response.get_json()
            print(f"✓ Admin login successful")
            print(f"  Token: {data['access_token'][:50]}...")
            print(f"  Role: {data['role']}")
            return True
        else:
            print(f"✗ Admin login failed: {response.status_code}")
            print(f"  Response: {response.get_json()}")
            return False

def test_librarian_login():
    """Test librarian login"""
    print("\n=== TEST 2: Librarian Login ===")
    with app.test_client() as client:
        response = client.post('/login', 
            json={'email': 'librarian1@library.com', 'password': 'librarian123', 'role': 'librarian'}
        )
        if response.status_code == 200:
            data = response.get_json()
            print(f"✓ Librarian login successful")
            print(f"  Token: {data['access_token'][:50]}...")
            print(f"  Role: {data['role']}")
            return True
        else:
            print(f"✗ Librarian login failed: {response.status_code}")
            return False

def test_student_login():
    """Test student login"""
    print("\n=== TEST 3: Student Login ===")
    with app.test_client() as client:
        response = client.post('/login', 
            json={'email': 'student1@library.com', 'password': 'student123', 'role': 'student'}
        )
        if response.status_code == 200:
            data = response.get_json()
            print(f"✓ Student login successful")
            print(f"  Token: {data['access_token'][:50]}...")
            print(f"  Role: {data['role']}")
            return True
        else:
            print(f"✗ Student login failed: {response.status_code}")
            return False

def test_profile_retrieval():
    """Test profile retrieval with token"""
    print("\n=== TEST 4: Profile Retrieval ===")
    with app.test_client() as client:
        # First login to get token
        login_response = client.post('/login', 
            json={'email': 'admin@library.com', 'password': 'admin123', 'role': 'admin'}
        )
        if login_response.status_code != 200:
            print(f"✗ Could not login to test profile")
            return False
        
        token = login_response.get_json()['access_token']
        
        # Then retrieve profile
        profile_response = client.get('/profile',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if profile_response.status_code == 200:
            profile = profile_response.get_json()
            print(f"✓ Profile retrieval successful")
            print(f"  Email: {profile['email']}")
            print(f"  Full Name: {profile['full_name']}")
            print(f"  Role: {profile['role']}")
            return True
        else:
            print(f"✗ Profile retrieval failed: {profile_response.status_code}")
            return False

def test_invalid_credentials():
    """Test login with invalid credentials"""
    print("\n=== TEST 5: Invalid Credentials ===")
    with app.test_client() as client:
        response = client.post('/login', 
            json={'email': 'admin@library.com', 'password': 'wrongpassword', 'role': 'admin'}
        )
        if response.status_code == 401:
            print(f"✓ Invalid credentials properly rejected")
            return True
        else:
            print(f"✗ Unexpected response: {response.status_code}")
            return False

def main():
    print("=" * 60)
    print("NashLibrary Authentication System - Comprehensive Test Suite")
    print("=" * 60)
    
    results = {
        'Admin Login': test_admin_login(),
        'Librarian Login': test_librarian_login(),
        'Student Login': test_student_login(),
        'Profile Retrieval': test_profile_retrieval(),
        'Invalid Credentials': test_invalid_credentials(),
    }
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! System is ready for deployment.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please review the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
