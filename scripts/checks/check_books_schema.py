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
        # Check all columns in books table
        cur.execute("DESCRIBE books")
        columns = cur.fetchall()
        print('Books table columns:')
        column_names = []
        for col in columns:
            column_names.append(col['Field'])
            print(f"  - {col['Field']}: {col['Type']}")
        
        print(f"\nColumns: {', '.join(column_names)}")
        print(f"\nHas 'available_copies': {'available_copies' in column_names}")
        print(f"Has 'total_copies': {'total_copies' in column_names}")
        
        # Show all books and their status
        print('\n=== ALL BOOKS ===')
        cur.execute("SELECT id, title, status FROM books ORDER BY id")
        books = cur.fetchall()
        for book in books:
            print(f"ID {book['id']}: {book['title']} - Status: {book['status']}")
        
finally:
    conn.close()
