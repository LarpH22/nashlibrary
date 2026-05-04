from ..database.db_connection import get_connection
from ...domain.repositories.book_repository import BookRepository
from .inventory_schema import ensure_inventory_schema


class BookRepositoryImpl(BookRepository):
    def add_book(self, title: str, author: str, isbn: str, available_copies: int = 1, total_copies: int = 1):
        with get_connection() as conn:
            try:
                ensure_inventory_schema(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO books (title, isbn, total_copies, added_date) VALUES (%s, %s, %s, NOW())",
                        (title, isbn, total_copies)
                    )
                    book_id = cur.lastrowid

                    cur.execute("INSERT IGNORE INTO authors (name) VALUES (%s)", (author,))
                    cur.execute("SELECT author_id FROM authors WHERE name=%s LIMIT 1", (author,))
                    author_record = cur.fetchone()
                    if author_record:
                        cur.execute(
                            "INSERT IGNORE INTO book_authors (book_id, author_id, author_order) VALUES (%s, %s, 1)",
                            (book_id, author_record['author_id'])
                        )
                    for sequence in range(1, max(int(total_copies or 1), 1) + 1):
                        cur.execute(
                            """
                            INSERT IGNORE INTO book_copies (book_id, copy_code, status)
                            VALUES (%s, %s, 'available')
                            """,
                            (book_id, f"{isbn or f'BOOK-{book_id}'}-{sequence:03d}"),
                        )
                conn.commit()
                return book_id
            except Exception:
                conn.rollback()
                raise

    def list_books(self):
        with get_connection() as conn:
            ensure_inventory_schema(conn)
            conn.commit()
            with conn.cursor() as cur:
                cur.execute(self._book_select_query())
                return cur.fetchall()

    def search_books(
        self,
        title: str = '',
        author: str = '',
        category: str = '',
        isbn: str = '',
        availability: str = '',
        history: str = '',
    ):
        with get_connection() as conn:
            ensure_inventory_schema(conn)
            conn.commit()
            with conn.cursor() as cur:
                where_clauses = []
                params = []

                if title:
                    where_clauses.append("(b.title LIKE %s OR b.description LIKE %s)")
                    keyword = f"%{title}%"
                    params.extend([keyword, keyword])

                if author:
                    where_clauses.append(
                        """
                        EXISTS (
                            SELECT 1
                            FROM book_authors filter_ba
                            JOIN authors filter_a ON filter_ba.author_id = filter_a.author_id
                            WHERE filter_ba.book_id = b.book_id
                              AND filter_a.name LIKE %s
                        )
                        """
                    )
                    params.append(f"%{author}%")

                if category:
                    where_clauses.append(
                        """
                        EXISTS (
                            SELECT 1
                            FROM books_categories filter_bc
                            JOIN categories filter_c ON filter_bc.category_id = filter_c.category_id
                            WHERE filter_bc.book_id = b.book_id
                              AND filter_c.name LIKE %s
                        )
                        """
                    )
                    params.append(f"%{category}%")

                if isbn:
                    where_clauses.append("b.isbn LIKE %s")
                    params.append(f"%{isbn}%")

                having_clauses = []
                normalized_availability = availability.strip().lower()
                if normalized_availability in ['available', 'true', '1', 'yes']:
                    having_clauses.append("available_copies > 0")
                elif normalized_availability in ['unavailable', 'out-of-stock', 'out_of_stock', 'false', '0', 'no']:
                    having_clauses.append("available_copies <= 0")
                elif normalized_availability in ['borrowed', 'checked-out', 'checked_out']:
                    having_clauses.append("borrowed_copies > 0")
                elif normalized_availability in ['lost', 'maintenance']:
                    having_clauses.append(
                        "SUM(CASE WHEN all_bc.status = %s THEN 1 ELSE 0 END) > 0"
                    )
                    params.append(normalized_availability)

                normalized_history = history.strip().lower()
                if normalized_history in ['borrowed', 'active', 'current', 'on-loan', 'on_loan']:
                    where_clauses.append(
                        """
                        EXISTS (
                            SELECT 1
                            FROM borrow_records filter_br
                            WHERE filter_br.book_id = b.book_id
                              AND filter_br.return_date IS NULL
                              AND filter_br.status IN ('active', 'borrowed', 'overdue')
                        )
                        """
                    )
                elif normalized_history in ['returned', 'return']:
                    where_clauses.append(
                        """
                        EXISTS (
                            SELECT 1
                            FROM borrow_records filter_br
                            WHERE filter_br.book_id = b.book_id
                              AND (
                                  filter_br.return_date IS NOT NULL
                                  OR filter_br.status = 'returned'
                              )
                        )
                        """
                    )
                elif normalized_history in ['any', 'all', 'has-history', 'has_history']:
                    where_clauses.append(
                        """
                        EXISTS (
                            SELECT 1
                            FROM borrow_records filter_br
                            WHERE filter_br.book_id = b.book_id
                        )
                        """
                    )
                elif normalized_history in ['none', 'never', 'no-history', 'no_history']:
                    where_clauses.append(
                        """
                        NOT EXISTS (
                            SELECT 1
                            FROM borrow_records filter_br
                            WHERE filter_br.book_id = b.book_id
                        )
                        """
                    )

                query = self._book_select_query(where_clauses, having_clauses)
                cur.execute(query, tuple(params))
                return cur.fetchall()

    def most_borrowed_books(self, limit: int = 5):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        b.book_id,
                        b.title,
                        b.author,
                        b.isbn,
                        b.category,
                        b.status,
                        b.available_copies,
                        b.total_copies,
                        COUNT(br.borrow_id) AS borrow_count
                    FROM books b
                    LEFT JOIN borrow_records br ON b.book_id = br.book_id
                    GROUP BY b.book_id, b.title, b.author, b.isbn, b.category, b.status, b.available_copies, b.total_copies
                    ORDER BY borrow_count DESC, b.title ASC
                    LIMIT %s
                    """,
                    (limit,)
                )
                return cur.fetchall()

    def find_by_id(self, book_id: int):
        with get_connection() as conn:
            ensure_inventory_schema(conn)
            conn.commit()
            with conn.cursor() as cur:
                cur.execute(self._book_select_query(["b.book_id=%s"]), (book_id,))
                return cur.fetchone()

    def update_book_status(self, book_id: int, status: str, available_copies: int | None = None):
        with get_connection() as conn:
            ensure_inventory_schema(conn)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE book_copies
                    SET status=%s
                    WHERE book_id=%s
                    ORDER BY copy_id
                    LIMIT 1
                    """,
                    (status, book_id),
                )
                conn.commit()
                return cur.rowcount > 0

    def _book_select_query(self, where_clauses=None, having_clauses=None):
        where_clauses = where_clauses or []
        having_clauses = having_clauses or []

        where_clause = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ''
        having_clause = f" HAVING {' AND '.join(having_clauses)}" if having_clauses else ''

        return f"""
            SELECT
                b.book_id,
                b.isbn,
                b.title,
                COALESCE(GROUP_CONCAT(DISTINCT a.name ORDER BY ba.author_order SEPARATOR ', '), '') AS author,
                COALESCE(GROUP_CONCAT(DISTINCT c.name ORDER BY c.name SEPARATOR ', '), '') AS category,
                b.total_copies,
                COUNT(DISTINCT CASE WHEN all_bc.status = 'available' THEN all_bc.copy_id END) AS available_copies,
                COUNT(DISTINCT CASE WHEN all_bc.status = 'borrowed' THEN all_bc.copy_id END) AS borrowed_copies,
                COUNT(DISTINCT all_bc.copy_id) AS copy_count,
                COALESCE(GROUP_CONCAT(DISTINCT all_bc.status ORDER BY all_bc.status SEPARATOR ', '), '') AS copy_statuses,
                COUNT(DISTINCT CASE
                    WHEN br.return_date IS NULL AND br.status IN ('active', 'borrowed', 'overdue')
                    THEN br.borrow_id
                END) AS active_borrow_count,
                COUNT(DISTINCT CASE
                    WHEN br.return_date IS NOT NULL OR br.status = 'returned'
                    THEN br.borrow_id
                END) AS returned_borrow_count,
                CASE
                    WHEN COUNT(DISTINCT CASE WHEN all_bc.status = 'available' THEN all_bc.copy_id END) > 0 THEN 'available'
                    WHEN COUNT(DISTINCT CASE WHEN all_bc.status = 'borrowed' THEN all_bc.copy_id END) > 0 THEN 'borrowed'
                    WHEN COUNT(DISTINCT all_bc.copy_id) = 0 THEN 'unavailable'
                    WHEN COUNT(DISTINCT CASE WHEN all_bc.status = 'maintenance' THEN all_bc.copy_id END) > 0 THEN 'maintenance'
                    WHEN COUNT(DISTINCT CASE WHEN all_bc.status = 'lost' THEN all_bc.copy_id END) > 0 THEN 'lost'
                    ELSE 'borrowed'
                END AS status
            FROM books b
            LEFT JOIN book_authors ba ON b.book_id = ba.book_id
            LEFT JOIN authors a ON ba.author_id = a.author_id
            LEFT JOIN books_categories bc ON b.book_id = bc.book_id
            LEFT JOIN categories c ON bc.category_id = c.category_id
            LEFT JOIN book_copies all_bc ON b.book_id = all_bc.book_id
            LEFT JOIN borrow_records br ON b.book_id = br.book_id
            {where_clause}
            GROUP BY b.book_id, b.isbn, b.title, b.total_copies
            {having_clause}
            ORDER BY b.title ASC
        """
