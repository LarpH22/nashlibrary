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
        # Get the schema of the books table
        cur.execute("DESCRIBE books")
        columns = cur.fetchall()
        print('=== BOOKS TABLE SCHEMA ===')
        for col in columns:
            print(f"{col['Field']}: {col['Type']} - Null: {col['Null']}, Default: {col['Default']}")
        
        print('\n=== FIXING THE ISSUE ===')
        print('Updating 1984 book status to available...')
        cur.execute("UPDATE books SET status='available' WHERE id=2")
        conn.commit()
        print(f'Rows affected: {cur.rowcount}')
        
        # Verify the fix
        print('\n=== VERIFICATION ===')
        cur.execute("SELECT id, title, status FROM books WHERE id=2")
        book = cur.fetchone()
        print(f"ID: {book['id']}, Title: {book['title']}, Status: {book['status']}")
        
finally:
    conn.close()
