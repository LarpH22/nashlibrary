#!/usr/bin/env python3
"""
Seed data restoration script for NashLibrary
Inserts main admin, librarian, and sample books/authors/categories
"""

import pymysql
from werkzeug.security import generate_password_hash
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.config import Config

def get_connection():
    return pymysql.connect(
        host=Config.DB_HOST,
        port=int(Config.DB_PORT),
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        charset='utf8mb4'
    )

def seed_accounts():
    """Insert admin and librarian accounts"""
    print("Seeding user accounts...")

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Admin account
            admin_email = "ralphrolandb30@gmail.com"
            admin_password = "Farmville"
            admin_hash = generate_password_hash(admin_password)

            try:
                cur.execute("""
                    INSERT INTO admins (email, password_hash, full_name, admin_level, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                    ON DUPLICATE KEY UPDATE
                    password_hash = VALUES(password_hash),
                    full_name = VALUES(full_name),
                    admin_level = VALUES(admin_level),
                    status = VALUES(status)
                """, (admin_email, admin_hash, "Ralph Roland B30", "super", "active"))
                print(f"✓ Admin account: {admin_email}")
            except Exception as e:
                print(f"✗ Admin insert failed: {e}")

            # Librarian account
            librarian_email = "nashandreimonteiro@gmail.com"
            librarian_password = "Farmville2"
            librarian_hash = generate_password_hash(librarian_password)

            try:
                cur.execute("""
                    INSERT INTO librarians (email, password_hash, full_name, employee_id, position, department, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    ON DUPLICATE KEY UPDATE
                    password_hash = VALUES(password_hash),
                    full_name = VALUES(full_name),
                    position = VALUES(position),
                    department = VALUES(department),
                    status = VALUES(status)
                """, (librarian_email, librarian_hash, "Nash Andre I. Monteiro", "LIB001", "Senior Librarian", "Library Management", "active"))
                print(f"✓ Librarian account: {librarian_email}")
            except Exception as e:
                print(f"✗ Librarian insert failed: {e}")

        conn.commit()

def seed_categories():
    """Insert book categories"""
    print("Seeding categories...")

    categories = [
        ("Fiction", "Fictional literature and novels"),
        ("Non-Fiction", "Educational and informative books"),
        ("Science", "Scientific and technical books"),
        ("History", "Historical books and biographies"),
        ("Technology", "Computer science and programming books"),
        ("Literature", "Classic and modern literature"),
        ("Mathematics", "Mathematics and statistics books"),
        ("Philosophy", "Philosophy and critical thinking"),
        ("Art", "Art and design books"),
        ("Business", "Business and management books")
    ]

    with get_connection() as conn:
        with conn.cursor() as cur:
            for name, desc in categories:
                try:
                    cur.execute("""
                        INSERT INTO categories (name, description, created_at)
                        VALUES (%s, %s, NOW())
                        ON DUPLICATE KEY UPDATE
                        description = VALUES(description)
                    """, (name, desc))
                except Exception as e:
                    print(f"✗ Category insert failed for {name}: {e}")

        conn.commit()
    print("✓ Categories seeded")

def seed_authors():
    """Insert book authors"""
    print("Seeding authors...")

    authors = [
        "J.K. Rowling",
        "George R.R. Martin",
        "Stephen King",
        "Agatha Christie",
        "Isaac Asimov",
        "Arthur C. Clarke",
        "Douglas Adams",
        "Neil Gaiman",
        "Terry Pratchett",
        "Philip K. Dick",
        "Frank Herbert",
        "William Gibson",
        "Cormac McCarthy",
        "Margaret Atwood",
        "Ursula K. Le Guin",
        "Octavia Butler",
        "Haruki Murakami",
        "Chimamanda Ngozi Adichie",
        "Yuval Noah Harari",
        "Michelle Obama"
    ]

    with get_connection() as conn:
        with conn.cursor() as cur:
            for name in authors:
                try:
                    cur.execute("""
                        INSERT INTO authors (name, created_at)
                        VALUES (%s, NOW())
                        ON DUPLICATE KEY UPDATE
                        name = VALUES(name)
                    """, (name,))
                except Exception as e:
                    print(f"✗ Author insert failed for {name}: {e}")

        conn.commit()
    print("✓ Authors seeded")

def seed_books():
    """Insert sample books with authors and categories"""
    print("Seeding books...")

    books_data = [
        {
            "isbn": "9780439708180",
            "title": "Harry Potter and the Sorcerer's Stone",
            "publisher": "Scholastic",
            "publication_year": 1997,
            "description": "The first book in the Harry Potter series",
            "total_copies": 5,
            "location": "Fiction-A1",
            "authors": ["J.K. Rowling"],
            "categories": ["Fiction", "Literature"]
        },
        {
            "isbn": "9780553103540",
            "title": "A Game of Thrones",
            "publisher": "Bantam Books",
            "publication_year": 1996,
            "description": "The first book in A Song of Ice and Fire series",
            "total_copies": 3,
            "location": "Fiction-A2",
            "authors": ["George R.R. Martin"],
            "categories": ["Fiction", "Literature"]
        },
        {
            "isbn": "9780307277671",
            "title": "The Road",
            "publisher": "Alfred A. Knopf",
            "publication_year": 2006,
            "description": "A post-apocalyptic novel about a father and son",
            "total_copies": 2,
            "location": "Fiction-A3",
            "authors": ["Cormac McCarthy"],
            "categories": ["Fiction", "Literature"]
        },
        {
            "isbn": "9780062315007",
            "title": "Sapiens: A Brief History of Humankind",
            "publisher": "Harper",
            "publication_year": 2014,
            "description": "A book about the history of humanity",
            "total_copies": 4,
            "location": "Non-Fiction-B1",
            "authors": ["Yuval Noah Harari"],
            "categories": ["Non-Fiction", "History"]
        },
        {
            "isbn": "9780060555665",
            "title": "Becoming",
            "publisher": "Crown",
            "publication_year": 2018,
            "description": "Michelle Obama's memoir",
            "total_copies": 3,
            "location": "Non-Fiction-B2",
            "authors": ["Michelle Obama"],
            "categories": ["Non-Fiction", "History"]
        },
        {
            "isbn": "9780132350884",
            "title": "Clean Code: A Handbook of Agile Software Craftsmanship",
            "publisher": "Prentice Hall",
            "publication_year": 2008,
            "description": "A book about writing clean, maintainable code",
            "total_copies": 2,
            "location": "Technology-C1",
            "authors": ["Robert C. Martin"],
            "categories": ["Technology", "Non-Fiction"]
        },
        {
            "isbn": "9780596517748",
            "title": "JavaScript: The Good Parts",
            "publisher": "O'Reilly Media",
            "publication_year": 2008,
            "description": "A guide to the best features of JavaScript",
            "total_copies": 3,
            "location": "Technology-C2",
            "authors": ["Douglas Crockford"],
            "categories": ["Technology", "Non-Fiction"]
        },
        {
            "isbn": "9780262033848",
            "title": "Introduction to Algorithms",
            "publisher": "MIT Press",
            "publication_year": 2009,
            "description": "A comprehensive textbook on algorithms",
            "total_copies": 1,
            "location": "Technology-C3",
            "authors": ["Thomas H. Cormen", "Charles E. Leiserson", "Ronald L. Rivest", "Clifford Stein"],
            "categories": ["Technology", "Mathematics", "Non-Fiction"]
        }
    ]

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Get librarian_id for added_by
            cur.execute("SELECT librarian_id FROM librarians WHERE email = %s", ("nashandreimonteiro@gmail.com",))
            librarian = cur.fetchone()
            librarian_id = librarian['librarian_id'] if librarian else None

            for book_data in books_data:
                try:
                    # Insert book
                    cur.execute("""
                        INSERT INTO books (isbn, title, publisher, publication_year, description, total_copies, location, added_by, added_date, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        ON DUPLICATE KEY UPDATE
                        title = VALUES(title),
                        publisher = VALUES(publisher),
                        publication_year = VALUES(publication_year),
                        description = VALUES(description),
                        total_copies = VALUES(total_copies),
                        location = VALUES(location)
                    """, (
                        book_data["isbn"],
                        book_data["title"],
                        book_data["publisher"],
                        book_data["publication_year"],
                        book_data["description"],
                        book_data["total_copies"],
                        book_data["location"],
                        librarian_id
                    ))

                    book_id = cur.lastrowid

                    # Insert authors
                    for author_name in book_data["authors"]:
                        cur.execute("SELECT author_id FROM authors WHERE name = %s", (author_name,))
                        author = cur.fetchone()
                        if author:
                            cur.execute("""
                                INSERT INTO book_authors (book_id, author_id, author_order)
                                VALUES (%s, %s, 1)
                                ON DUPLICATE KEY UPDATE
                                author_order = VALUES(author_order)
                            """, (book_id, author['author_id']))

                    # Insert categories
                    for category_name in book_data["categories"]:
                        cur.execute("SELECT category_id FROM categories WHERE name = %s", (category_name,))
                        category = cur.fetchone()
                        if category:
                            cur.execute("""
                                INSERT INTO books_categories (book_id, category_id)
                                VALUES (%s, %s)
                                ON DUPLICATE KEY UPDATE
                                book_id = VALUES(book_id)
                            """, (book_id, category['category_id']))

                except Exception as e:
                    print(f"✗ Book insert failed for {book_data['title']}: {e}")

        conn.commit()
    print("✓ Books seeded")

def verify_data():
    """Verify that data was inserted correctly"""
    print("Verifying seed data...")

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Check accounts
            cur.execute("SELECT COUNT(*) as count FROM admins")
            admin_count = cur.fetchone()['count']
            print(f"✓ Admins: {admin_count}")

            cur.execute("SELECT COUNT(*) as count FROM librarians")
            librarian_count = cur.fetchone()['count']
            print(f"✓ Librarians: {librarian_count}")

            # Check books data
            cur.execute("SELECT COUNT(*) as count FROM books")
            book_count = cur.fetchone()['count']
            print(f"✓ Books: {book_count}")

            cur.execute("SELECT COUNT(*) as count FROM authors")
            author_count = cur.fetchone()['count']
            print(f"✓ Authors: {author_count}")

            cur.execute("SELECT COUNT(*) as count FROM categories")
            category_count = cur.fetchone()['count']
            print(f"✓ Categories: {category_count}")

            # Check relationships
            cur.execute("SELECT COUNT(*) as count FROM book_authors")
            book_author_count = cur.fetchone()['count']
            print(f"✓ Book-Author relationships: {book_author_count}")

            cur.execute("SELECT COUNT(*) as count FROM books_categories")
            book_category_count = cur.fetchone()['count']
            print(f"✓ Book-Category relationships: {book_category_count}")

def main():
    print("=" * 50)
    print("NASHLIBRARY DATABASE SEED RESTORATION")
    print("=" * 50)

    try:
        seed_accounts()
        seed_categories()
        seed_authors()
        seed_books()
        verify_data()

        print("=" * 50)
        print("✓ Database restoration completed successfully!")
        print("✓ Admin: ralphrolandb30@gmail.com / Farmville")
        print("✓ Librarian: nashandreimonteiro@gmail.com / Farmville2")
        print("✓ Sample books, authors, and categories inserted")
        print("=" * 50)

    except Exception as e:
        print(f"✗ Restoration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()