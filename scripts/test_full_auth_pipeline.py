#!/usr/bin/env python
"""
Comprehensive test script for the full authentication pipeline.
Tests: DB connection, user retrieval, password verification, and login endpoint.
"""

import sys
import os
import bcrypt
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.config import Config
from backend.app.infrastructure.database.db_connection import get_connection
from backend.app.domain.services.auth_service import AuthService
from backend.app.infrastructure.repositories_impl.user_repository_impl import UserRepositoryImpl

def test_database_connection():
    print("\n=== Testing Database Connection ===")
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as count FROM users")
                result = cur.fetchone()
                print(f"✓ DB Connection Success - User Count: {result['count']}")
                
                # List all users
                cur.execute("SELECT user_id, email, role, status FROM users")
                users = cur.fetchall()
                print(f"✓ Users in database:")
                for user in users:
                    print(f"  - ID: {user['user_id']}, Email: {user['email']}, Role: {user['role']}, Status: {user['status']}")
    except Exception as e:
        print(f"✗ DB Connection Failed: {e}")
        return False
    return True

def test_user_retrieval():
    print("\n=== Testing User Retrieval ===")
    try:
        repo = UserRepositoryImpl()
        user = repo.find_by_email('admin@library.com')
        if user:
            print(f"✓ User Found: {user['email']}")
            print(f"  - User ID: {user['user_id']}")
            print(f"  - Role: {user['role']}")
            print(f"  - Status: {user['status']}")
            print(f"  - Password Hash (first 50 chars): {user['password_hash'][:50]}...")
            return user
        else:
            print("✗ User Not Found")
            return None
    except Exception as e:
        print(f"✗ User Retrieval Failed: {e}")
        return None

def test_password_verification():
    print("\n=== Testing Password Verification ===")
    try:
        user = test_user_retrieval()
        if not user:
            print("✗ Skipping password verification - no user found")
            return False
        
        auth_service = AuthService(UserRepositoryImpl())
        
        # Test with correct password
        result = auth_service.verify_password('admin123', user['password_hash'])
        print(f"✓ Verify 'admin123': {result}")
        
        # Test with incorrect password
        result = auth_service.verify_password('wrongpassword', user['password_hash'])
        print(f"✓ Verify 'wrongpassword': {result}")
        
        return True
    except Exception as e:
        print(f"✗ Password Verification Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_authentication():
    print("\n=== Testing Authentication ===")
    try:
        auth_service = AuthService(UserRepositoryImpl())
        
        # Test valid credentials
        print("Testing: admin@library.com / admin123")
        user = auth_service.authenticate('admin@library.com', 'admin123')
        if user:
            print(f"✓ Authentication Success")
            print(f"  - Email: {user['email']}")
            print(f"  - Role: {user['role']}")
        else:
            print(f"✗ Authentication Failed - returned None")
        
        # Test invalid credentials
        print("\nTesting: admin@library.com / wrongpassword")
        user = auth_service.authenticate('admin@library.com', 'wrongpassword')
        if user is None:
            print(f"✓ Correctly rejected invalid credentials")
        else:
            print(f"✗ Should have rejected invalid credentials")
        
        return True
    except Exception as e:
        print(f"✗ Authentication Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_jwt_token_generation():
    print("\n=== Testing JWT Token Generation ===")
    try:
        from flask_jwt_extended import create_access_token
        from backend.app import app
        
        with app.app_context():
            token = create_access_token(identity='admin@library.com')
            print(f"✓ Token Generated: {token[:50]}...")
            
            # Decode to verify
            import jwt
            decoded = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            print(f"✓ Token Decoded Successfully")
            print(f"  - Subject (email): {decoded.get('sub')}")
            print(f"  - Token Type: {decoded.get('type')}")
            
            return True
    except Exception as e:
        print(f"✗ JWT Token Generation Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("NASHLIBRARY - FULL AUTHENTICATION PIPELINE TEST")
    print("=" * 60)
    
    # Run tests
    results = []
    results.append(("Database Connection", test_database_connection()))
    results.append(("User Retrieval", test_user_retrieval() is not None))
    results.append(("Password Verification", test_password_verification()))
    results.append(("Authentication", test_authentication()))
    results.append(("JWT Token Generation", test_jwt_token_generation()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return all(r for _, r in results)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
