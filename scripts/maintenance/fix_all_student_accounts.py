#!/usr/bin/env python
import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from backend.app.infrastructure.database.db_connection import get_connection

try:
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Fix all pending student accounts
            print('Fixing all pending student accounts...\n')
            
            # Get all pending students
            cur.execute("SELECT student_id, email, full_name FROM students WHERE status='pending'")
            pending_students = cur.fetchall()
            
            for student in pending_students:
                email = student['email']
                cur.execute(
                    """UPDATE students 
                       SET status='active', email_verified=1 
                       WHERE email=%s""",
                    (email,)
                )
                conn.commit()
                print(f'✓ Fixed: {email}')
            
            # Verify all fixes
            print('\n=== All Student Accounts ===')
            cur.execute("SELECT student_id, email, full_name, status, email_verified FROM students")
            students = cur.fetchall()
            for student in students:
                status_ok = "✓" if student['status'] == 'active' and student['email_verified'] else "✗"
                print(f"{status_ok} {student['email']} - status: {student['status']}, verified: {student['email_verified']}")
                
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
