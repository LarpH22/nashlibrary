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
cursor = conn.cursor()

# First, let's check what books exist
cursor.execute('SELECT book_id, title FROM books LIMIT 10')
books = cursor.fetchall()
print(f"Sample books in database: {len(books)}")
for book_id, title in books:
    print(f"  Book ID {book_id}: {title}")

# Now add more test ebooks to some of these books
test_ebooks = [
    (books[1][0], "Programming Fundamentals", "programming_fundamentals.pdf", "pdf", 5120),
    (books[2][0], "Data Structures Guide", "data_structures.pdf", "pdf", 6200),
    (books[3][0], "Web Development Basics", "web_dev.epub", "epub", 4500),
    (books[4][0], "Advanced Python", "advanced_python.pdf", "pdf", 7100),
    (books[5][0], "Database Design", "database_design.pdf", "pdf", 5800),
    (books[6][0], "Software Engineering", "software_eng.pdf", "pdf", 8200),
    (books[7][0], "Cloud Computing", "cloud_computing.epub", "epub", 6700),
    (books[8][0], "AI & Machine Learning", "ai_ml.pdf", "pdf", 9300),
]

for book_id, title, filename, file_type, file_size in test_ebooks:
    stored_filename = f"test_{title.replace(' ', '_')}.{file_type}"
    file_path = f"backend/uploads/ebooks/{stored_filename}"
    
    cursor.execute(
        """INSERT INTO ebooks (book_id, title, original_filename, stored_filename, file_path, file_type, file_size, uploaded_at, uploaded_by_role, uploaded_by_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s)""",
        (book_id, title, filename, stored_filename, file_path, file_type, file_size, 'librarian', 1)
    )

conn.commit()

# Now count the ebooks again
cursor.execute('SELECT COUNT(*) as total FROM ebooks')
count = cursor.fetchone()
print(f"\nTotal ebooks after adding test data: {count[0]}")

# List all ebooks
cursor.execute('SELECT ebook_id, title, book_id FROM ebooks ORDER BY uploaded_at DESC')
results = cursor.fetchall()
for row in results:
    print(f"  ID: {row[0]}, Title: {row[1]}, Book ID: {row[2]}")

cursor.close()
conn.close()
print("\nTest ebooks added successfully!")
