import requests
import json

BASE_URL = "http://localhost:5000"

# First, login to get a JWT token
login_data = {
    "email": "student1@library.com",
    "password": "student123"
}

print("=" * 60)
print("1. Testing Login Endpoint")
print("=" * 60)

response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json=login_data,
    headers={"Content-Type": "application/json"}
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    login_response = response.json()
    token = login_response.get("access_token")
    print(f"\n✓ Login successful")
    print(f"Token: {token[:50]}...")
    
    # Now test the loans endpoint with the token
    print("\n" + "=" * 60)
    print("2. Testing /api/loans/student Endpoint")
    print("=" * 60)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        f"{BASE_URL}/api/loans/student",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Response: {response.text}")
    
    try:
        data = response.json()
        print(f"\nParsed JSON: {json.dumps(data, indent=2)}")
    except:
        print("Could not parse response as JSON")
    
    if response.status_code == 200:
        print("\n✓ Loans endpoint successful")
        loans = response.json()
        print(f"Loans count: {len(loans) if isinstance(loans, list) else 'N/A'}")
        print(f"Loans data: {json.dumps(loans, indent=2)}")
    else:
        print("\n✗ Loans endpoint failed")
        
else:
    print(f"\n✗ Login failed")
