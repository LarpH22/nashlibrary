import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import app

print("=" * 60)
print("Testing Flask app with enhanced error handling")
print("=" * 60)

# Disable error handlers temporarily to see the real error
@app.errorhandler(Exception)
def debug_error_handler(e):
    import traceback
    print(f"\n!!! UNHANDLED EXCEPTION: {type(e).__name__}: {str(e)}")
    traceback.print_exc()
    raise  # Re-raise to see full error

try:
    with app.test_client() as client:
        # Login
        login_response = client.post('/api/auth/login', json={
            'email': 'student1@library.com',
            'password': 'student123'
        })
        
        if login_response.status_code == 200:
            token = login_response.get_json().get('access_token')
            
            # Test loans endpoint
            print("\nCalling /api/loans/student...")
            loans_response = client.get(
                '/api/loans/student',
                headers={'Authorization': f'Bearer {token}'}
            )
            print(f"Status: {loans_response.status_code}")
            print(f"Response: {loans_response.get_data(as_text=True)}")
            
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
