from typing import Any

from ...domain.repositories.seed_repository import SeedRepository
from ..database.db_connection import get_connection


class SeedRepositoryImpl(SeedRepository):
    def _open_connection(self):
        return get_connection()

    def ensure_inventory_schema(self):
        conn = self._open_connection()
        try:
            cur = conn.cursor()
            cur.execute(
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            )
            cur.close()
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_existing_book_isbns(self) -> set:
        conn = self._open_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT isbn FROM books WHERE isbn IS NOT NULL")
            isbns = {row['isbn'] for row in cur.fetchall() if row.get('isbn')}
            cur.close()
            return isbns
        finally:
            conn.close()

    def get_or_create_author(self, name: str, conn: Any = None) -> int:
        if conn is None:
            conn = self._open_connection()
            close_conn = True
        else:
            close_conn = False

        try:
            cur = conn.cursor()
            cur.execute("SELECT author_id FROM authors WHERE name=%s LIMIT 1", (name,))
            existing = cur.fetchone()
            if existing:
                cur.close()
                return existing['author_id']

            cur.execute("INSERT INTO authors (name) VALUES (%s)", (name,))
            author_id = cur.lastrowid
            cur.close()
            return author_id
        finally:
            if close_conn:
                conn.close()

    def get_or_create_category(self, name: str, conn: Any = None) -> int:
        if conn is None:
            conn = self._open_connection()
            close_conn = True
        else:
            close_conn = False

        try:
            cur = conn.cursor()
            cur.execute("SELECT category_id FROM categories WHERE name=%s LIMIT 1", (name,))
            existing = cur.fetchone()
            if existing:
                cur.close()
                return existing['category_id']

            cur.execute("INSERT INTO categories (name) VALUES (%s)", (name,))
            category_id = cur.lastrowid
            cur.close()
            return category_id
        finally:
            if close_conn:
                conn.close()

    def create_book(self, title: str, author_id: int, category_id: int, isbn: str, published_date, cover_image_url: str, conn: Any = None) -> int:
        if conn is None:
            conn = self._open_connection()
            close_conn = True
        else:
            close_conn = False

        try:
            cur = conn.cursor()
            publication_year = getattr(published_date, 'year', None)
            cur.execute(
                "INSERT INTO books (title, isbn, publication_year, total_copies, added_date) VALUES (%s, %s, %s, 1, NOW())",
                (title, isbn, publication_year),
            )
            book_id = cur.lastrowid
            cur.execute(
                "INSERT IGNORE INTO book_authors (book_id, author_id, author_order) VALUES (%s, %s, 1)",
                (book_id, author_id),
            )
            cur.execute(
                "INSERT IGNORE INTO books_categories (book_id, category_id) VALUES (%s, %s)",
                (book_id, category_id),
            )
            cur.close()
            return book_id
        finally:
            if close_conn:
                conn.close()

    def create_book_copy(self, book_id: int, copy_code: str, status: str, location: str, conn: Any = None) -> int:
        if conn is None:
            conn = self._open_connection()
            close_conn = True
        else:
            close_conn = False

        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO book_copies (book_id, copy_code, status, location) VALUES (%s, %s, %s, %s)",
                (book_id, copy_code, status, location),
            )
            copy_id = cur.lastrowid
            cur.close()
            return copy_id
        finally:
            if close_conn:
                conn.close()

    def run_in_transaction(self, callback):
        conn = self._open_connection()
        try:
            result = callback(conn)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
