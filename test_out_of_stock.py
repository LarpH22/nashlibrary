#!/usr/bin/env python3
"""Create out-of-stock test data and verify search filtering"""
import sys
sys.path.insert(0, '.')

from backend.config import Config
import pymysql

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
    cur = conn.cursor()

    # Get first 3 books and set all their copies to 'borrowed'
    cur.execute('SELECT book_id FROM books LIMIT 3')
    test_books = cur.fetchall()

    for book in test_books:
        book_id = book['book_id']
        
        # Set all copies for this book to 'borrowed'
        cur.execute(
            'UPDATE book_copies SET status = %s WHERE book_id = %s',
            ('borrowed', book_id)
        )
        print(f"Set all copies of book {book_id} to 'borrowed'")

    conn.commit()

    # Now verify the out-of-stock search works
    print("\n--- Testing out-of-stock search ---")
    cur.execute('''
        SELECT 
            b.book_id, 
            b.title,
            COUNT(DISTINCT bc.copy_id) as total_copies,
            SUM(CASE WHEN bc.status = "available" THEN 1 ELSE 0 END) as available_copies,
            GROUP_CONCAT(DISTINCT bc.status SEPARATOR ",") as statuses
        FROM books b
        LEFT JOIN book_copies bc ON b.book_id = bc.book_id
        WHERE b.book_id IN (1, 2, 3)
        GROUP BY b.book_id
    ''')

    books = cur.fetchall()
    print(f"\nBooks with 0 available copies:")
    for book in books:
        print(f"  ID: {book['book_id']}, Title: {book['title']}, Total: {book['total_copies']}, Available: {book['available_copies']}, Statuses: {book['statuses']}")

    print("\n✓ Test data created. Try searching for 'Out of Stock' in the catalog now.")

finally:
    if cur:
        cur.close()
    if conn:
        conn.close()
