#!/usr/bin/env python
import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from backend.app.infrastructure.database.db_connection import get_connection

try:
    with get_connection() as conn:
        with conn.cursor() as cur:
            print('=== STUDENTS TABLE ===')
            cur.execute('SELECT student_id, email, full_name, status, email_verified FROM students LIMIT 10')
            rows = cur.fetchall()
            for row in rows:
                print(row)
                
            print('\n=== REGISTRATION REQUESTS ===')
            cur.execute('SELECT request_id, email, full_name, status, email_verified FROM registration_requests LIMIT 10')
            rows = cur.fetchall()
            for row in rows:
                print(row)
                
            print('\n=== LIBRARIANS TABLE ===')
            cur.execute('SELECT librarian_id, email, full_name, status FROM librarians LIMIT 5')
            rows = cur.fetchall()
            for row in rows:
                print(row)
                
            print('\n=== ADMINS TABLE ===')
            cur.execute('SELECT admin_id, email, full_name, status FROM admins LIMIT 5')
            rows = cur.fetchall()
            for row in rows:
                print(row)
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
