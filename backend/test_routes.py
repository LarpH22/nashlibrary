#!/usr/bin/env python
import sys
import os

# Add parent directory to path so we can import backend module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Importing app...")
from backend.app import app

print("App imported successfully!")
print(f"\n=== Flask App Info ===")
print(f"App name: {app.name}")
print(f"Debug: {app.debug}")
print(f"Testing: {app.testing}")

print(f"\n=== Registered Routes ===")
for rule in app.url_map.iter_rules():
    methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
    print(f"{rule.rule:30} -> {rule.endpoint:30} [{methods}]")

print(f"\n=== Testing Route Matching ===")
with app.test_client() as client:
    print("\nTesting GET /register:")
    response = client.get('/register')
    print(f"Status: {response.status_code}")
    print(f"Data: {response.get_json()}")
    
    print("\nTesting GET /login:")
    response = client.get('/login')
    print(f"Status: {response.status_code}")
    print(f"Data: {response.get_json()}")
    
    print("\nTesting GET /:")
    response = client.get('/')
    print(f"Status: {response.status_code}")
    print(f"Data (truncated): {str(response.get_json())[:100]}")
