import sys
import traceback

sys.path.insert(0, 'c:/Users/admin/Documents/nashlibrary')

from backend.app import app
from backend.app.presentation.controllers.auth_controller import AuthController
from backend.app.presentation.controllers.loan_controller import LoanController

with app.app_context():
    with app.test_client() as client:
        # Login as existing student to get a token
        login_resp = client.post('/api/auth/login', json={
            'email': 'student1@library.com',
            'password': 'student123'
        })
        print('login status', login_resp.status_code)
        print('login body', login_resp.get_json())
        token = login_resp.get_json().get('access_token')

        headers = {'Authorization': f'Bearer {token}'}
        resp = client.get('/api/loans/student', headers=headers)
        print('loan status', resp.status_code)
        print('loan body', resp.get_data(as_text=True))
        if resp.status_code >= 500:
            print('--- error detail ---')
            try:
                data = resp.get_json()
                print(data)
            except Exception:
                traceback.print_exc()
