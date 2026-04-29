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
        # Find 1984 book
        cur.execute("SELECT * FROM books WHERE title='1984' LIMIT 1")
        book = cur.fetchone()
        if book:
            print('=== BOOK DETAILS ===')
            for k, v in book.items():
                print(f'{k}: {v}')
            
            book_id = book.get('book_id') or book.get('id')
            print(f'\n=== BORROW RECORDS FOR THIS BOOK ===')
            cur.execute('SELECT * FROM borrow_records WHERE book_id=%s ORDER BY borrow_id DESC LIMIT 5', (book_id,))
            records = cur.fetchall()
            if records:
                for i, record in enumerate(records):
                    print(f'\n--- Record {i+1} ---')
                    for k, v in record.items():
                        print(f'{k}: {v}')
            else:
                print('No borrow records found')
        else:
            print('Book not found')
finally:
    conn.close()
