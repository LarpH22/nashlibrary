import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Checking imports and syntax")
print("=" * 60)

try:
    print("\n1. Importing Flask app...")
    from backend.app import app
    print("✓ Flask app imported")
    
    print("\n2. Testing the loan routes...")
    with app.test_client() as client:
        print("✓ Test client created")
        
        # Get a token first
        login_response = client.post('/api/auth/login', json={
            'email': 'student1@library.com',
            'password': 'student123'
        })
        print(f"✓ Login response: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token = login_response.get_json().get('access_token')
            print(f"✓ Got token")
            
            # Now test the loans endpoint
            print("\n3. Testing /api/loans/student endpoint...")
            loans_response = client.get(
                '/api/loans/student',
                headers={'Authorization': f'Bearer {token}'}
            )
            print(f"✓ Loans response: {loans_response.status_code}")
            print(f"  Response data: {loans_response.get_data(as_text=True)[:500]}")
            
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
