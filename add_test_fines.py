#!/usr/bin/env python3
import pymysql
from datetime import datetime, timedelta

try:
    conn = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password='root',
        database='nashlibrary_db',
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4'
    )
    
    with conn.cursor() as cur:
        # Get Bob's student ID
        cur.execute("SELECT u.user_id, s.student_id FROM users u JOIN students s ON u.user_id = s.user_id WHERE u.email='bob@example.com'")
        user = cur.fetchone()
        
        if not user:
            print("Bob not found!")
            conn.close()
            exit(1)
        
        student_id = user['student_id']
        print(f"Found Bob with student_id: {student_id}")
        
        # Get Bob's first borrow record
        cur.execute("SELECT borrow_id FROM borrow_records WHERE student_id=%s LIMIT 1", (student_id,))
        borrow = cur.fetchone()
        
        if borrow:
            borrow_id = borrow['borrow_id']
            
            # Add 3 test fines
            fines_to_add = [
                (borrow_id, student_id, 2.50, 'Overdue book - 5 days late', 'pending'),
                (borrow_id, student_id, 1.50, 'Overdue book - 3 days late', 'paid'),
                (borrow_id, student_id, 5.00, 'Damaged book cover', 'pending'),
            ]
            
            for borrow_id_val, student_id_val, amount, reason, status in fines_to_add:
                cur.execute(
                    '''INSERT INTO fines (borrow_id, student_id, amount, reason, status, issued_date, issued_by)
                       VALUES (%s, %s, %s, %s, %s, %s, NULL)''',
                    (borrow_id_val, student_id_val, amount, reason, status, datetime.now().date())
                )
            
            conn.commit()
            print(f"Added 3 test fines for Bob")
            
            # Verify
            cur.execute("SELECT * FROM fines WHERE student_id=%s", (student_id,))
            fines = cur.fetchall()
            print(f"\nFines for Bob (total: {len(fines)}):")
            for fine in fines:
                print(f"  - ${fine['amount']} ({fine['status']}): {fine['reason']}")
        else:
            print("No borrow records found for Bob")
    
    conn.close()
    print("\n✅ Test fines added successfully!")
    print("Refresh your browser to see the Fines Card on the dashboard.")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
