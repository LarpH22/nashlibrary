#!/usr/bin/env python
import pymysql
from backend.config import Config

conn = pymysql.connect(
    host=Config.DB_HOST,
    port=int(Config.DB_PORT),
    user=Config.DB_USER,
    password=Config.DB_PASSWORD,
    database=Config.DB_NAME,
    cursorclass=pymysql.cursors.DictCursor,
    charset='utf8mb4'
)

try:
    with conn.cursor() as cur:
        # Find all books with status='borrowed' but all borrow records returned
        print('=== CHECKING FOR SIMILAR ISSUES ===')
        cur.execute("""
            SELECT b.id, b.title, b.status,
                   COUNT(br.borrow_id) AS total_borrows,
                   SUM(CASE WHEN br.status='returned' THEN 1 ELSE 0 END) AS returned_count,
                   SUM(CASE WHEN br.status='borrowed' THEN 1 ELSE 0 END) AS borrowed_count
            FROM books b
            LEFT JOIN borrow_records br ON b.id = br.book_id
            GROUP BY b.id, b.title, b.status
            HAVING b.status='borrowed' AND (borrowed_count = 0 OR borrowed_count IS NULL)
            ORDER BY b.id
        """)
        
        problematic_books = cur.fetchall()
        if problematic_books:
            print(f'Found {len(problematic_books)} books with status="borrowed" but no active borrows:\n')
            for book in problematic_books:
                print(f"ID: {book['id']}, Title: {book['title']}")
                print(f"  Status: {book['status']}")
                print(f"  Total Borrows: {book['total_borrows']}, Returned: {book['returned_count']}, Active: {book['borrowed_count']}")
                
                # Fix it
                cur.execute("UPDATE books SET status='available' WHERE id=%s", (book['id'],))
                print(f"  ✓ Fixed - Updated to 'available'")
                print()
            
            conn.commit()
            print(f'\n✓ All {len(problematic_books)} books have been fixed!')
        else:
            print('✓ No problematic books found - all books have correct status!')
        
finally:
    conn.close()
