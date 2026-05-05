#!/usr/bin/env python
import sys
sys.path.insert(0, '/'.join(__file__.split('\\')[:-1]))

import mysql.connector
from backend.config import Config

conn = mysql.connector.connect(
    host=Config.DB_HOST,
    user=Config.DB_USER,
    password=Config.DB_PASSWORD,
    database=Config.DB_NAME
)
cursor = conn.cursor(dictionary=True)

# Count all ebooks
cursor.execute('SELECT COUNT(*) as total FROM ebooks')
count = cursor.fetchone()
print(f"Total ebooks in database: {count['total']}")

# List all ebooks
cursor.execute('SELECT ebook_id, title, book_id FROM ebooks ORDER BY uploaded_at DESC')
results = cursor.fetchall()
for row in results:
    print(f"  ID: {row['ebook_id']}, Title: {row['title']}, Book ID: {row['book_id']}")

cursor.close()
conn.close()
