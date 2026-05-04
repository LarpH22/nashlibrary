import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.presentation.controllers.loan_controller import LoanController
from unittest.mock import Mock

print("=" * 60)
print("Testing LoanController Directly")
print("=" * 60)

try:
    controller = LoanController()
    print("✓ Controller created")
    
    # Create a mock current_user with student_id
    current_user = {
        'email': 'student1@library.com',
        'role': 'student',
        'student_id': 1
    }
    
    # Mock the Flask request context
    from flask import Flask, g
    app = Flask(__name__)
    with app.app_context():
        print("\n✓ Flask app context created")
        print(f"  Calling controller with current_user: {current_user}")
        
        response = controller.list_student_loans(current_user)
        print(f"✓ Response received: {response}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
