#!/usr/bin/env python
"""
Seed 500 normalized library books into MySQL.

The script is deterministic and idempotent: running it again reuses the same
ISBNs, authors, categories, and relationship rows instead of inserting copies.
"""

import argparse
import random
import sys
from datetime import date, timedelta
from pathlib import Path

import pymysql

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.config import Config


SEED = 20260505
DEFAULT_BOOK_COUNT = 500

CATEGORIES = [
    "Art",
    "Biography",
    "Business",
    "Computer Science",
    "Education",
    "Engineering",
    "Environment",
    "Fantasy",
    "Health",
    "History",
    "Law",
    "Literature",
    "Mathematics",
    "Music",
    "Philosophy",
    "Politics",
    "Psychology",
    "Science",
    "Self-Help",
    "Technology",
]

AUTHORS = [
    "Avery Bennett",
    "Maya Chen",
    "Noah Whitaker",
    "Sofia Ramirez",
    "Ethan Brooks",
    "Amara Okafor",
    "Julian Hart",
    "Priya Nair",
    "Lena Fischer",
    "Marcus Reed",
    "Elena Kovacs",
    "Thomas Delgado",
    "Nadia Rahman",
    "Caleb Morrison",
    "Iris Campbell",
    "Jonas Eriksson",
    "Hannah Sinclair",
    "Mateo Alvarez",
    "Grace Holloway",
    "Owen Tan",
    "Clara Weston",
    "Samuel Ortega",
    "Mina Park",
    "Felix Monroe",
    "Leila Haddad",
    "Isaac Turner",
    "Celine Moreau",
    "Aaron Santos",
    "Nora Fitzgerald",
    "Vikram Shah",
    "Tessa Morgan",
    "Daniel Kim",
    "Yara Mansour",
    "Miles Carter",
    "Anika Rao",
    "Theo Wallace",
    "June Nakamura",
    "Rafael Costa",
    "Miriam Blake",
    "Ezra Collins",
]

TITLE_PATTERNS = [
    "The {subject} Handbook",
    "A Field Guide to {subject}",
    "{adjective} {subject}",
    "{subject} in Practice",
    "The {noun} of {subject}",
    "{subject}: Modern Approaches",
    "Understanding {subject}",
    "The Complete {subject} Companion",
    "{adjective} Lessons in {subject}",
    "Principles of {subject}",
]

SUBJECTS_BY_CATEGORY = {
    "Art": ["Visual Culture", "Studio Practice", "Modern Design", "Color Theory", "Museum Studies"],
    "Biography": ["Public Lives", "Private Letters", "Creative Courage", "Life Stories", "Working Legacies"],
    "Business": ["Strategic Growth", "Market Systems", "Team Leadership", "Financial Decisions", "Startup Operations"],
    "Computer Science": ["Data Systems", "Software Design", "Machine Learning", "Secure Networks", "Algorithmic Thinking"],
    "Education": ["Classroom Research", "Learning Design", "Student Success", "Curriculum Planning", "Assessment"],
    "Engineering": ["Urban Infrastructure", "Sustainable Materials", "Control Systems", "Product Design", "Applied Mechanics"],
    "Environment": ["Climate Resilience", "Forest Futures", "Ocean Recovery", "Urban Ecology", "Conservation Policy"],
    "Fantasy": ["Ashen Kingdoms", "Moonlit Realms", "Old Magic", "Dragon Courts", "Hidden Gates"],
    "Health": ["Public Wellness", "Nutrition Science", "Community Care", "Healthy Aging", "Clinical Habits"],
    "History": ["World Revolutions", "Ancient Cities", "Maritime Empires", "Social Change", "Everyday Archives"],
    "Law": ["Civil Rights", "Digital Privacy", "Public Policy", "Legal Reasoning", "International Justice"],
    "Literature": ["Contemporary Fiction", "Poetic Forms", "Narrative Craft", "World Novels", "Critical Reading"],
    "Mathematics": ["Applied Statistics", "Discrete Models", "Number Theory", "Mathematical Proof", "Quantitative Reasoning"],
    "Music": ["Jazz Traditions", "Sound Production", "Music Theory", "Global Rhythms", "Performance Practice"],
    "Philosophy": ["Moral Questions", "Practical Ethics", "Political Thought", "Human Meaning", "Logic"],
    "Politics": ["Democratic Reform", "Civic Power", "Global Affairs", "Public Institutions", "Policy Debates"],
    "Psychology": ["Human Behavior", "Memory Science", "Social Minds", "Emotional Health", "Cognitive Bias"],
    "Science": ["Deep Space", "Cell Biology", "Earth Systems", "Experimental Methods", "Scientific Discovery"],
    "Self-Help": ["Focused Habits", "Resilient Living", "Personal Systems", "Daily Discipline", "Purposeful Work"],
    "Technology": ["Digital Transformation", "Cloud Platforms", "Robotics", "Human-Centered AI", "Future Interfaces"],
}

ADJECTIVES = [
    "Adaptive",
    "Applied",
    "Clear",
    "Contemporary",
    "Creative",
    "Essential",
    "Everyday",
    "Future",
    "Global",
    "Human",
    "Practical",
    "Quiet",
    "Resilient",
    "Sustainable",
    "Working",
]

NOUNS = [
    "Architecture",
    "Atlas",
    "Foundations",
    "Framework",
    "Language",
    "Map",
    "Method",
    "Patterns",
    "Practice",
    "Story",
]

PUBLISHERS = [
    "Northbridge Press",
    "Harbor Academic",
    "Cedar House",
    "Blue Finch Books",
    "Meridian Learning",
    "Silverline Publishing",
    "Riverton Media",
    "Oak & Lantern",
]


def connect():
    return pymysql.connect(
        host=Config.DB_HOST,
        port=int(Config.DB_PORT),
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        charset="utf8mb4",
    )


def column_exists(cursor, table_name, column_name):
    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = %s
          AND column_name = %s
        """,
        (table_name, column_name),
    )
    return cursor.fetchone()["count"] > 0


def ensure_seed_schema(cursor):
    if not column_exists(cursor, "books", "published_date"):
        cursor.execute("ALTER TABLE books ADD COLUMN published_date DATE NULL AFTER publication_year")

    if not column_exists(cursor, "books", "cover_image_url"):
        cursor.execute("ALTER TABLE books ADD COLUMN cover_image_url VARCHAR(500) NULL AFTER description")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS book_copies (
            copy_id INT PRIMARY KEY AUTO_INCREMENT,
            book_id INT NOT NULL,
            copy_code VARCHAR(60) NOT NULL UNIQUE,
            status ENUM('available', 'borrowed', 'lost', 'maintenance') NOT NULL DEFAULT 'available',
            location VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
            INDEX idx_book_id (book_id),
            INDEX idx_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )


def isbn13_check_digit(digits12):
    total = sum(int(char) * (1 if index % 2 == 0 else 3) for index, char in enumerate(digits12))
    remainder = total % 10
    return "0" if remainder == 0 else str(10 - remainder)


def make_isbn(sequence):
    digits12 = f"978{SEED % 1000:03d}{sequence:06d}"
    return digits12 + isbn13_check_digit(digits12)


def random_published_date(rng):
    end = date.today()
    start = end - timedelta(days=365 * 20)
    return start + timedelta(days=rng.randint(0, (end - start).days))


def build_books(count):
    rng = random.Random(SEED)
    books = []

    for index in range(1, count + 1):
        category = CATEGORIES[(index - 1) % len(CATEGORIES)]
        author = AUTHORS[(index - 1) % len(AUTHORS)]
        subject = rng.choice(SUBJECTS_BY_CATEGORY[category])
        title = rng.choice(TITLE_PATTERNS).format(
            adjective=rng.choice(ADJECTIVES),
            noun=rng.choice(NOUNS),
            subject=subject,
        )
        edition_suffix = f"Volume {(index - 1) // len(CATEGORIES) + 1}"
        isbn = make_isbn(index)
        published_date = random_published_date(rng)
        total_copies = rng.randint(1, 5)

        books.append(
            {
                "title": f"{title}: {edition_suffix}",
                "author": author,
                "category": category,
                "isbn": isbn,
                "publisher": rng.choice(PUBLISHERS),
                "published_date": published_date,
                "publication_year": published_date.year,
                "description": f"A realistic library edition covering {subject.lower()} for students and general readers.",
                "cover_image_url": f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg",
                "total_copies": total_copies,
                "location": f"Shelf {category[:3].upper()}-{rng.randint(1, 48):02d}",
            }
        )

    return books


def get_or_create_author(cursor, name):
    cursor.execute(
        """
        INSERT INTO authors (name)
        VALUES (%s)
        ON DUPLICATE KEY UPDATE author_id = LAST_INSERT_ID(author_id)
        """,
        (name,),
    )
    return cursor.lastrowid


def get_or_create_category(cursor, name):
    cursor.execute(
        """
        INSERT INTO categories (name)
        VALUES (%s)
        ON DUPLICATE KEY UPDATE category_id = LAST_INSERT_ID(category_id)
        """,
        (name,),
    )
    return cursor.lastrowid


def upsert_book(cursor, book):
    cursor.execute(
        """
        INSERT INTO books (
            isbn, title, publisher, publication_year, published_date, description,
            cover_image_url, total_copies, location, added_date
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE
            book_id = LAST_INSERT_ID(book_id),
            title = VALUES(title),
            publisher = VALUES(publisher),
            publication_year = VALUES(publication_year),
            published_date = VALUES(published_date),
            description = VALUES(description),
            cover_image_url = VALUES(cover_image_url),
            total_copies = GREATEST(total_copies, VALUES(total_copies)),
            location = VALUES(location)
        """,
        (
            book["isbn"],
            book["title"],
            book["publisher"],
            book["publication_year"],
            book["published_date"],
            book["description"],
            book["cover_image_url"],
            book["total_copies"],
            book["location"],
        ),
    )
    return cursor.lastrowid


def link_author(cursor, book_id, author_id):
    cursor.execute(
        """
        INSERT IGNORE INTO book_authors (book_id, author_id, author_order)
        VALUES (%s, %s, 1)
        """,
        (book_id, author_id),
    )


def link_category(cursor, book_id, category_id):
    cursor.execute(
        """
        INSERT IGNORE INTO books_categories (book_id, category_id)
        VALUES (%s, %s)
        """,
        (book_id, category_id),
    )


def ensure_copies(cursor, book_id, isbn, total_copies, location):
    inserted = 0
    for sequence in range(1, total_copies + 1):
        cursor.execute(
            """
            INSERT IGNORE INTO book_copies (book_id, copy_code, status, location)
            VALUES (%s, %s, 'available', %s)
            """,
            (book_id, f"{isbn}-{sequence:03d}", location),
        )
        inserted += cursor.rowcount
    return inserted


def seed_books(count):
    books = build_books(count)
    metrics = {
        "requested": count,
        "books_inserted_or_updated": 0,
        "authors_linked": 0,
        "categories_linked": 0,
        "copies_inserted": 0,
    }

    conn = connect()
    try:
        with conn.cursor() as cursor:
            ensure_seed_schema(cursor)
            for book in books:
                author_id = get_or_create_author(cursor, book["author"])
                category_id = get_or_create_category(cursor, book["category"])
                book_id = upsert_book(cursor, book)
                link_author(cursor, book_id, author_id)
                link_category(cursor, book_id, category_id)
                metrics["copies_inserted"] += ensure_copies(
                    cursor,
                    book_id,
                    book["isbn"],
                    book["total_copies"],
                    book["location"],
                )
                metrics["books_inserted_or_updated"] += 1
                metrics["authors_linked"] += 1
                metrics["categories_linked"] += 1

        conn.commit()
        return metrics
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Seed normalized Library Management System books.")
    parser.add_argument("--count", type=int, default=DEFAULT_BOOK_COUNT, help="Number of deterministic books to seed.")
    args = parser.parse_args()

    if args.count < 1:
        raise SystemExit("--count must be at least 1")

    metrics = seed_books(args.count)
    print("Normalized book seed complete")
    for key, value in metrics.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
