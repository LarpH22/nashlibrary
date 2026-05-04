#!/usr/bin/env python
import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from backend.app.infrastructure.database.db_connection import get_connection

try:
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Fix the student account
            email = 'mojadopaulinealexa218@gmail.com'
            
            # Update the student record to active with verified email
            cur.execute(
                """UPDATE students 
                   SET status='active', email_verified=1 
                   WHERE email=%s""",
                (email,)
            )
            conn.commit()
            print(f'✓ Fixed student account: {email}')
            print(f'  - status: pending → active')
            print(f'  - email_verified: 0 → 1')
            
            # Verify the fix
            cur.execute(
                "SELECT student_id, email, full_name, status, email_verified FROM students WHERE email=%s",
                (email,)
            )
            row = cur.fetchone()
            print(f'\nVerified fix:')
            print(f'  {row}')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
