#!/usr/bin/env python
import os
import sys
import traceback

sys.path.insert(0, 'backend')
os.environ.setdefault('DB_PORT', '3307')
os.environ.setdefault('DB_PASSWORD', '')

try:
    print("1. Importing app...")
    from backend.app import app
    print("   App imported")
    
    print("2. Testing basic connection...")
    from backend.app import get_connection
    conn = get_connection()
    conn.close()
    print("   Database connected")
    
    print("3. Creating test client...")
    with app.test_client() as client:
        print("   Test client created")
        
        print("4. Making login request...")
        response = client.post('/login', json={
            'username': 'ralphrolandb30@gmail.com',
            'password': 'Farmville'
        })
        print(f"   Response: {response.status_code}")
        print(f"   Data: {response.get_json()}")
        
except Exception as e:
    print("\nError occurred:")
    print(f"  {str(e)}")
    print("\nFull traceback:")
    traceback.print_exc()
