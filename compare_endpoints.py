import requests
import json

BASE_URL = "http://localhost:5000"

# First, login to get a JWT token
login_data = {
    "email": "student1@library.com",
    "password": "student123"
}

response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json=login_data,
    headers={"Content-Type": "application/json"}
)

if response.status_code == 200:
    token = response.json().get("access_token")
    print(f"✓ Login successful")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test both endpoints
    endpoints = [
        ("/api/students/profile", "Student Profile"),
        ("/api/loans/student", "Student Loans"),
    ]
    
    for endpoint, name in endpoints:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        print(f"\n{name}:")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
