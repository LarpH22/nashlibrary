from ..database.db_connection import get_connection
from ...domain.repositories.book_repository import BookRepository


class BookRepositoryImpl(BookRepository):
    def add_book(self, title: str, author: str, isbn: str, available_copies: int = 1, total_copies: int = 1):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO books (title, author, isbn, status, available_copies, total_copies, created_at) VALUES (%s, %s, %s, %s, %s, %s, NOW())",
                    (title, author, isbn, 'available', available_copies, total_copies)
                )
                conn.commit()
                return cur.lastrowid

    def list_books(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM books ORDER BY title ASC")
                return cur.fetchall()

    def find_by_id(self, book_id: int):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM books WHERE book_id=%s LIMIT 1", (book_id,))
                return cur.fetchone()

    def update_book_status(self, book_id: int, status: str, available_copies: int | None = None):
        with get_connection() as conn:
            with conn.cursor() as cur:
                if available_copies is not None:
                    cur.execute(
                        "UPDATE books SET status=%s, available_copies=%s WHERE book_id=%s",
                        (status, available_copies, book_id)
                    )
                else:
                    cur.execute(
                        "UPDATE books SET status=%s WHERE book_id=%s",
                        (status, book_id)
                    )
                conn.commit()
                return cur.rowcount > 0
