import sys
import traceback
import logging

# Enable all logging
logging.basicConfig(level=logging.DEBUG)

try:
    from backend.app import app
    
    # Create test client
    client = app.test_client()
    
    print("Making login request...")
    response = client.post('/login', 
        json={'email': 'admin@library.com', 'password': 'admin123', 'role': 'admin'},
        follow_redirects=False
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.get_json()}")
    
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)
