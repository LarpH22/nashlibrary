#!/usr/bin/env python
import requests
import json

# Login
login_response = requests.post('http://localhost:5000/api/auth/login', json={
    'email': 'student1@library.com',
    'password': 'student123'
})
token = login_response.json().get('access_token')
print(f"Login status: {login_response.status_code}")
print(f"Token: {token[:20]}...")

# Make request with detailed logging
response = requests.get(
    'http://localhost:5000/api/loans/student',
    headers={'Authorization': f'Bearer {token}'}
)

print(f"\nRequest details:")
print(f"  URL: {response.request.url}")
print(f"  Method: {response.request.method}")
print(f"  Headers: {dict(response.request.headers)}")

print(f"\nResponse details:")
print(f"  Status: {response.status_code}")
print(f"  Headers: {dict(response.headers)}")
print(f"  Body: {response.text}")

# Try the profile endpoint for comparison
profile_response = requests.get(
    'http://localhost:5000/api/students/profile',
    headers={'Authorization': f'Bearer {token}'}
)

print(f"\nProfile endpoint (for comparison):")
print(f"  Status: {profile_response.status_code}")
print(f"  Body: {profile_response.text}")