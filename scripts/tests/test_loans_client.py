#!/usr/bin/env python
import os
import sys

# Add paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

# Set environment
os.environ.setdefault('USE_DEV_FRONTEND', 'false')
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import app

# Test the loan endpoint directly using Flask test client
with app.test_client() as client:
    # Create a token
    from flask_jwt_extended import create_access_token
    from datetime import timedelta
    
    with app.app_context():
        token = create_access_token(
            identity='student1@library.com',
            additional_claims={
                'email': 'student1@library.com',
                'role': 'student',
                'student_id': 1,
                'librarian_id': None,
                'admin_id': None
            },
            expires_delta=timedelta(hours=1)
        )
    
    # Test the loans endpoint
    response = client.get(
        '/api/loans/student',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    print(f'Test Client Response:')
    print(f'  Status: {response.status_code}')
    print(f'  Body: {response.data.decode()}')
    print(f'  Content-Type: {response.content_type}')
