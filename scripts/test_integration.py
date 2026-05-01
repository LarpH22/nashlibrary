#!/usr/bin/env python
"""
Integration test for the complete NashLibrary authentication pipeline.
Tests the full flow: API server, database, auth pipeline, and response handling.
"""

import sys
import os
import requests
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.config import Config
from backend.app.infrastructure.database.db_connection import get_connection

API_BASE_URL = 'http://localhost:5000'
TEST_TIMEOUT = 5

def test_server_health():
    """Test if the server is running and responding."""
    print("\n=== Testing Server Health ===")
    try:
        response = requests.get(f'{API_BASE_URL}/', timeout=TEST_TIMEOUT)
        print(f"✓ Server is running (Status: {response.status_code})")
        return True
    except requests.exceptions.ConnectionError:
        print("✗ Server is not running. Please start the server with: python backend/run_server.py")
        return False
    except Exception as e:
        print(f"✗ Server health check failed: {e}")
        return False

def test_login_endpoint_invalid_credentials():
    """Test login with invalid credentials."""
    print("\n=== Testing Login Endpoint (Invalid Credentials) ===")
    try:
        response = requests.post(
            f'{API_BASE_URL}/login',
            json={'email': 'nonexistent@library.com', 'password': 'wrongpassword'},
            timeout=TEST_TIMEOUT
        )
        if response.status_code == 401:
            print(f"✓ Correctly rejected invalid credentials (Status: {response.status_code})")
            print(f"  Response: {response.json()}")
            return True
        else:
            print(f"✗ Unexpected status code: {response.status_code}")
            print(f"  Response: {response.json()}")
            return False
    except Exception as e:
        print(f"✗ Login test failed: {e}")
        return False

def test_login_endpoint_valid_credentials():
    """Test login with valid credentials."""
    print("\n=== Testing Login Endpoint (Valid Credentials) ===")
    try:
        response = requests.post(
            f'{API_BASE_URL}/login',
            json={'email': 'admin@library.com', 'password': 'admin123'},
            timeout=TEST_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'access_token' in data:
                print(f"✓ Login successful (Status: {response.status_code})")
                print(f"  - Token: {data['access_token'][:50]}...")
                print(f"  - Role: {data.get('role', 'N/A')}")
                return data['access_token']
            else:
                print(f"✗ No access token in response")
                print(f"  Response: {data}")
                return None
        else:
            print(f"✗ Login failed with status: {response.status_code}")
            print(f"  Response: {response.json()}")
            return None
    except Exception as e:
        print(f"✗ Login test failed: {e}")
        return False

def test_protected_endpoint(token):
    """Test accessing a protected endpoint with a valid token."""
    print("\n=== Testing Protected Endpoint (/profile) ===")
    if not token:
        print("✗ Skipping - no valid token available")
        return False
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(
            f'{API_BASE_URL}/profile',
            headers=headers,
            timeout=TEST_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Protected endpoint access successful (Status: {response.status_code})")
            print(f"  - Email: {data.get('email')}")
            print(f"  - Role: {data.get('role')}")
            return True
        else:
            print(f"✗ Protected endpoint failed with status: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Protected endpoint test failed: {e}")
        return False

def test_cors_headers():
    """Test that CORS headers are present."""
    print("\n=== Testing CORS Headers ===")
    try:
        response = requests.options(
            f'{API_BASE_URL}/login',
            timeout=TEST_TIMEOUT
        )
        cors_origin = response.headers.get('Access-Control-Allow-Origin')
        if cors_origin:
            print(f"✓ CORS is enabled")
            print(f"  - Allow-Origin: {cors_origin}")
            return True
        else:
            print(f"✗ CORS headers not found")
            return False
    except Exception as e:
        print(f"✗ CORS test failed: {e}")
        return False

def test_register_endpoint():
    """Test user registration."""
    print("\n=== Testing Register Endpoint ===")
    try:
        test_email = f'testuser{int(time.time())}@library.com'
        response = requests.post(
            f'{API_BASE_URL}/register',
            json={
                'email': test_email,
                'password': 'testpass123',
                'full_name': 'Test User'
            },
            timeout=TEST_TIMEOUT
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✓ Registration successful (Status: {response.status_code})")
            print(f"  - Message: {data.get('message')}")
            print(f"  - User ID: {data.get('user_id')}")
            return True
        elif response.status_code == 400:
            print(f"✓ Registration validation working (Status: {response.status_code})")
            print(f"  - Response: {response.json()}")
            return True
        else:
            print(f"✗ Registration failed with status: {response.status_code}")
            print(f"  Response: {response.json()}")
            return False
    except Exception as e:
        print(f"✗ Registration test failed: {e}")
        return False

def test_database_connectivity():
    """Test database connectivity."""
    print("\n=== Testing Database Connectivity ===")
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as count FROM users")
                result = cur.fetchone()
                user_count = result['count']
                print(f"✓ Database connected - User count: {user_count}")
                return True
    except Exception as e:
        print(f"✗ Database connectivity failed: {e}")
        return False

def main():
    print("=" * 70)
    print("NASHLIBRARY - FULL INTEGRATION TEST")
    print("=" * 70)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Database: {Config.DB_NAME} @ {Config.DB_HOST}:{Config.DB_PORT}")
    
    # Run tests
    results = []
    results.append(("Database Connectivity", test_database_connectivity()))
    
    if not results[-1][1]:
        print("\n✗ Database is not accessible. Cannot continue with other tests.")
        return False
    
    results.append(("Server Health", test_server_health()))
    
    if not results[-1][1]:
        print("\n✗ Server is not running. Please start it with: python backend/run_server.py")
        return False
    
    results.append(("CORS Headers", test_cors_headers()))
    results.append(("Invalid Credentials", test_login_endpoint_invalid_credentials()))
    
    token = test_login_endpoint_valid_credentials()
    results.append(("Valid Credentials", token is not False and token is not None))
    
    if token:
        results.append(("Protected Endpoint", test_protected_endpoint(token)))
    else:
        results.append(("Protected Endpoint", False))
    
    results.append(("Register Endpoint", test_register_endpoint()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All integration tests passed! The system is ready.")
    else:
        print("\n✗ Some tests failed. Please review the output above.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
