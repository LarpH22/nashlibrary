#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')
from backend.config import Config
import mysql.connector

conn = mysql.connector.connect(
    host=Config.MYSQL_HOST,
    user=Config.MYSQL_USER,
    password=Config.MYSQL_PASSWORD,
    database=Config.MYSQL_DB
)
cur = conn.cursor(dictionary=True)

# Check books and their copies
cur.execute('''
    SELECT 
        b.book_id, 
        b.title,
        COUNT(DISTINCT bc.copy_id) as total_copies,
        SUM(CASE WHEN bc.status = "available" THEN 1 ELSE 0 END) as available_copies,
        GROUP_CONCAT(DISTINCT bc.status SEPARATOR ",") as statuses
    FROM books b
    LEFT JOIN book_copies bc ON b.book_id = bc.book_id
    GROUP BY b.book_id
    ORDER BY b.book_id
    LIMIT 30
''')
books = cur.fetchall()
print('Books in database:')
print(f'Total books: {len(books)}')
for book in books:
    print(f"  ID: {book['book_id']}, Title: {book['title']}, Total: {book['total_copies']}, Available: {book['available_copies']}, Statuses: {book['statuses']}")

print('\n\nBooks with 0 available copies:')
cur.execute('''
    SELECT 
        b.book_id, 
        b.title,
        COUNT(DISTINCT bc.copy_id) as total_copies,
        GROUP_CONCAT(DISTINCT bc.status SEPARATOR ",") as statuses
    FROM books b
    LEFT JOIN book_copies bc ON b.book_id = bc.book_id
    GROUP BY b.book_id
    HAVING SUM(CASE WHEN bc.status = "available" THEN 1 ELSE 0 END) <= 0
    LIMIT 30
''')
out_of_stock = cur.fetchall()
print(f'Out of stock books: {len(out_of_stock)}')
for book in out_of_stock:
    print(f"  ID: {book['book_id']}, Title: {book['title']}, Total: {book['total_copies']}, Statuses: {book['statuses']}")

cur.close()
conn.close()
