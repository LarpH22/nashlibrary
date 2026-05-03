import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.infrastructure.database.db_connection import get_connection

print("=" * 60)
print("Testing Database Connection and Query")
print("=" * 60)

try:
    print("\n1. Connecting to database...")
    with get_connection() as conn:
        print("✓ Connected to database")
        
        print("\n2. Testing loans query for student_id=1...")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    br.borrow_id AS loan_id,
                    br.student_id,
                    br.book_id,
                    b.title AS book_title,
                    b.isbn,
                    b.publisher AS book_publisher,
                    b.publication_year,
                    br.borrow_date AS issue_date,
                    br.due_date,
                    br.return_date,
                    br.status,
                    CASE WHEN br.status = 'returned' THEN TRUE ELSE FALSE END AS returned
                FROM borrow_records br
                LEFT JOIN books b ON br.book_id = b.book_id
                WHERE br.student_id = %s
                ORDER BY br.borrow_date DESC
            """, (1,))
            loans = cur.fetchall()
            print(f"✓ Query executed. Got {len(loans)} loans")
            
            print("\n3. Loan data structure:")
            if loans:
                for i, loan in enumerate(loans):
                    print(f"\n  Loan {i}:")
                    for key, value in loan.items():
                        print(f"    {key}: {value} ({type(value).__name__})")
            else:
                print("  No loans found for student 1")
            
            print("\n4. Testing JSON serialization...")
            import json
            try:
                # Test with the loans as-is
                json_str = json.dumps(loans)
                print("✓ JSON serialization successful")
                print(f"  JSON length: {len(json_str)}")
            except TypeError as e:
                print(f"✗ JSON serialization failed: {e}")
                print(f"  Error type: {type(e).__name__}")
                
                # Try to identify which field is causing the issue
                if loans:
                    for key, value in loans[0].items():
                        try:
                            json.dumps({key: value})
                        except TypeError:
                            print(f"  Problem field: {key} = {value} ({type(value).__name__})")
                
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
