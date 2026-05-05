import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.infrastructure.database.db_connection import get_connection

print("=" * 60)
print("Checking Database Content")
print("=" * 60)

try:
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Check students
            print("\n1. Students in database:")
            cur.execute("SELECT student_id, email, full_name FROM students LIMIT 10")
            students = cur.fetchall()
            print(f"  Found {len(students)} students:")
            for st in students:
                print(f"    ID: {st['student_id']}, Email: {st['email']}, Name: {st['full_name']}")
            
            # Check books
            print("\n2. Books in database:")
            cur.execute("SELECT book_id, title FROM books LIMIT 10")
            books = cur.fetchall()
            print(f"  Found {len(books)} books")
            
            # Check borrow_records
            print("\n3. Borrow records in database:")
            cur.execute("SELECT br.borrow_id, br.student_id, br.book_id, br.status FROM borrow_records LIMIT 10")
            borrowings = cur.fetchall()
            print(f"  Found {len(borrowings)} borrow records:")
            for br in borrowings:
                print(f"    ID: {br['borrow_id']}, Student: {br['student_id']}, Book: {br['book_id']}, Status: {br['status']}")
            
            # Check for student_id=1 specifically
            print("\n4. Checking for student_id=1:")
            cur.execute("SELECT * FROM students WHERE student_id = 1")
            result = cur.fetchone()
            if result:
                print(f"  ✓ Student 1 exists: {result}")
            else:
                print(f"  ✗ Student 1 not found")
            
            # Check for any loans for student_id=1
            print("\n5. Checking for loans for student_id=1:")
            cur.execute("SELECT COUNT(*) as count FROM borrow_records WHERE student_id = 1")
            result = cur.fetchone()
            print(f"  Found {result['count']} loans")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
