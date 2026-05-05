import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.infrastructure.database.db_connection import get_connection

print("=" * 60)
print("Checking borrow_records table structure")
print("=" * 60)

try:
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Get table structure
            print("\n1. borrow_records table columns:")
            cur.execute("DESC borrow_records")
            columns = cur.fetchall()
            for col in columns:
                print(f"  - {col['Field']}: {col['Type']} (Null: {col['Null']}, Key: {col['Key']}, Default: {col['Default']})")
            
            # Get a sample row
            print("\n2. Sample borrow_records data:")
            cur.execute("SELECT * FROM borrow_records LIMIT 1")
            row = cur.fetchone()
            if row:
                print(f"  Columns: {list(row.keys())}")
                print(f"  Data: {row}")
            else:
                print("  No data in table")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
