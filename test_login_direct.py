#!/usr/bin/env python
import os
import sys
sys.path.insert(0, 'backend')

os.environ.setdefault('DB_PORT', '3307')
os.environ.setdefault('DB_PASSWORD', '')

from backend.app import app, login

# Test the login endpoint directly
with app.test_client() as client:
    # Test data
    test_data = {
        'username': 'ralphrolandb30@gmail.com',
        'password': 'Farmville'
    }
    
    print(f"Testing login with: {test_data}")
    
    # Make request
    response = client.post('/login', json=test_data)
    
    print(f"\nResponse status: {response.status_code}")
    print(f"Response data: {response.get_json()}")
    
    if response.status_code != 200:
        print("\nLogin failed")
    else:
        print("\nLogin successful")
