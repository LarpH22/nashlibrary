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
                        copy_code = f"{isbn or f'BOOK-{book_id}'}-{sequence:03d}"
                        cur.execute(
                            """
                            INSERT IGNORE INTO book_copies (book_id, copy_code, barcode_value, qr_token, status)
                            VALUES (%s, %s, %s, %s, 'available')
                            """,
                            (book_id, copy_code, copy_code, f"QR-{book_id}-{sequence:03d}-{copy_code}"),
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

    def list_books_missing_qr(self):
        with get_connection() as conn:
            ensure_inventory_schema(conn)
            conn.commit()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT book_id, title, qr_code_path
                    FROM books
                    WHERE qr_code_path IS NULL OR qr_code_path = ''
                    ORDER BY book_id ASC
                    """
                )
                return cur.fetchall()

    def search_books(
        self,
        title: str = '',
        author: str = '',
        category: str = '',
        isbn: str = '',
        availability: str = '',
        history: str = '',
        page: int | None = None,
        limit: int | None = None,
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
                count_query = self._book_count_query(where_clauses, having_clauses)
                cur.execute(count_query, tuple(params))
                count_row = cur.fetchone() or {}
                total = int(count_row.get('total') or 0)

                normalized_limit = max(1, min(int(limit or 0), 100)) if limit else None
                normalized_page = max(1, int(page or 1))

                if normalized_limit:
                    offset = (normalized_page - 1) * normalized_limit
                    query = f"{query}\nLIMIT %s OFFSET %s"
                    query_params = [*params, normalized_limit, offset]
                else:
                    query_params = params

                cur.execute(query, tuple(query_params))
                books = cur.fetchall()

                if not normalized_limit:
                    return books

                total_pages = max(1, (total + normalized_limit - 1) // normalized_limit)
                return {
                    'books': books,
                    'pagination': {
                        'page': normalized_page,
                        'limit': normalized_limit,
                        'total': total,
                        'total_pages': total_pages,
                    },
                }

    def most_borrowed_books(self, limit: int = 5):
        with get_connection() as conn:
            ensure_inventory_schema(conn)
            conn.commit()
            with conn.cursor() as cur:
                cur.execute(
                    """
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
                        COUNT(DISTINCT br.borrow_id) AS borrow_count,
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
                    GROUP BY b.book_id, b.isbn, b.title, b.total_copies
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

    def update_book_qr_code_path(self, book_id: int, qr_code_path: str):
        with get_connection() as conn:
            ensure_inventory_schema(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE books SET qr_code_path=%s WHERE book_id=%s",
                    (qr_code_path, book_id),
                )
                conn.commit()
                return cur.rowcount > 0

    def list_copies(self, book_id: int | None = None):
        with get_connection() as conn:
            ensure_inventory_schema(conn)
            conn.commit()
            with conn.cursor() as cur:
                params = []
                where_clause = ""
                if book_id is not None:
                    where_clause = "WHERE bc.book_id=%s"
                    params.append(book_id)
                cur.execute(
                    f"""
                    SELECT
                        bc.copy_id,
                        bc.book_id,
                        bc.copy_code,
                        bc.barcode_value,
                        bc.qr_token,
                        bc.status,
                        bc.location,
                        b.title AS book_title,
                        b.isbn,
                        COALESCE(GROUP_CONCAT(DISTINCT a.name ORDER BY ba.author_order SEPARATOR ', '), '') AS author
                    FROM book_copies bc
                    JOIN books b ON bc.book_id = b.book_id
                    LEFT JOIN book_authors ba ON b.book_id = ba.book_id
                    LEFT JOIN authors a ON ba.author_id = a.author_id
                    {where_clause}
                    GROUP BY bc.copy_id, bc.book_id, bc.copy_code, bc.barcode_value, bc.qr_token, bc.status, bc.location, b.title, b.isbn
                    ORDER BY b.title ASC, bc.copy_code ASC
                    """,
                    tuple(params),
                )
                return cur.fetchall()

    def find_copy_by_scan_code(self, scan_code: str):
        with get_connection() as conn:
            ensure_inventory_schema(conn)
            conn.commit()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        bc.copy_id,
                        bc.book_id,
                        bc.copy_code,
                        bc.barcode_value,
                        bc.qr_token,
                        bc.status,
                        b.title AS book_title,
                        b.isbn,
                        COALESCE(GROUP_CONCAT(DISTINCT a.name ORDER BY ba.author_order SEPARATOR ', '), '') AS author
                    FROM book_copies bc
                    JOIN books b ON bc.book_id = b.book_id
                    LEFT JOIN book_authors ba ON b.book_id = ba.book_id
                    LEFT JOIN authors a ON ba.author_id = a.author_id
                    WHERE bc.copy_code=%s OR bc.barcode_value=%s OR bc.qr_token=%s
                    GROUP BY bc.copy_id, bc.book_id, bc.copy_code, bc.barcode_value, bc.qr_token, bc.status, b.title, b.isbn
                    LIMIT 1
                    """,
                    (scan_code, scan_code, scan_code),
                )
                return cur.fetchone()

    def create_ebook(self, book_id: int, title: str, original_filename: str, stored_filename: str, file_path: str, file_type: str, file_size: int, uploaded_by_role: str, uploaded_by_id: int | None):
        with get_connection() as conn:
            try:
                ensure_inventory_schema(conn)
                with conn.cursor() as cur:
                    cur.execute("SELECT book_id FROM books WHERE book_id=%s LIMIT 1", (book_id,))
                    if not cur.fetchone():
                        raise ValueError("Book not found")
                    cur.execute(
                        """
                        INSERT INTO ebooks
                            (book_id, title, original_filename, stored_filename, file_path, file_type, file_size, uploaded_by_role, uploaded_by_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (book_id, title, original_filename, stored_filename, file_path, file_type, file_size, uploaded_by_role, uploaded_by_id),
                    )
                    ebook_id = cur.lastrowid
                conn.commit()
                return ebook_id
            except Exception:
                conn.rollback()
                raise

    def list_ebooks(self, book_id: int | None = None):
        with get_connection() as conn:
            ensure_inventory_schema(conn)
            conn.commit()
            with conn.cursor() as cur:
                params = []
                where_clause = ""
                if book_id is not None:
                    where_clause = "WHERE e.book_id=%s"
                    params.append(book_id)
                cur.execute(
                    f"""
                    SELECT
                        e.ebook_id,
                        e.book_id,
                        e.title,
                        e.original_filename,
                        e.file_type,
                        e.file_size,
                        e.uploaded_at,
                        e.qr_code_path,
                        b.title AS book_title,
                        b.isbn,
                        COALESCE(GROUP_CONCAT(DISTINCT a.name ORDER BY ba.author_order SEPARATOR ', '), '') AS author,
                        COALESCE(GROUP_CONCAT(DISTINCT c.name ORDER BY c.name SEPARATOR ', '), '') AS category
                    FROM ebooks e
                    JOIN books b ON e.book_id = b.book_id
                    LEFT JOIN book_authors ba ON b.book_id = ba.book_id
                    LEFT JOIN authors a ON ba.author_id = a.author_id
                    LEFT JOIN books_categories bc ON b.book_id = bc.book_id
                    LEFT JOIN categories c ON bc.category_id = c.category_id
                    {where_clause}
                    GROUP BY e.ebook_id, e.book_id, e.title, e.original_filename, e.file_type, e.file_size, e.uploaded_at, e.qr_code_path, b.title, b.isbn
                    ORDER BY e.uploaded_at DESC
                    """,
                    tuple(params),
                )
                return cur.fetchall()

    def list_ebooks_missing_qr(self):
        with get_connection() as conn:
            ensure_inventory_schema(conn)
            conn.commit()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT ebook_id, title, qr_code_path
                    FROM ebooks
                    WHERE qr_code_path IS NULL OR qr_code_path = ''
                    ORDER BY ebook_id ASC
                    """
                )
                return cur.fetchall()

    def find_ebook(self, ebook_id: int):
        with get_connection() as conn:
            ensure_inventory_schema(conn)
            conn.commit()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        e.*,
                        b.title AS book_title,
                        b.isbn,
                        COALESCE(GROUP_CONCAT(DISTINCT a.name ORDER BY ba.author_order SEPARATOR ', '), '') AS author,
                        COALESCE(GROUP_CONCAT(DISTINCT c.name ORDER BY c.name SEPARATOR ', '), '') AS category
                    FROM ebooks e
                    JOIN books b ON e.book_id = b.book_id
                    LEFT JOIN book_authors ba ON b.book_id = ba.book_id
                    LEFT JOIN authors a ON ba.author_id = a.author_id
                    LEFT JOIN books_categories bc ON b.book_id = bc.book_id
                    LEFT JOIN categories c ON bc.category_id = c.category_id
                    WHERE e.ebook_id=%s
                    GROUP BY e.ebook_id, e.book_id, e.title, e.original_filename, e.stored_filename, e.file_path,
                             e.file_type, e.file_size, e.access_level, e.uploaded_by_role, e.uploaded_by_id,
                             e.uploaded_at, e.qr_code_path, b.title, b.isbn
                    LIMIT 1
                    """,
                    (ebook_id,),
                )
                return cur.fetchone()

    def update_ebook_qr_code_path(self, ebook_id: int, qr_code_path: str):
        with get_connection() as conn:
            ensure_inventory_schema(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE ebooks SET qr_code_path=%s WHERE ebook_id=%s",
                    (qr_code_path, ebook_id),
                )
                conn.commit()
                return cur.rowcount > 0

    def get_ebook_delete_blockers(self, ebook_id: int):
        with get_connection() as conn:
            ensure_inventory_schema(conn)
            conn.commit()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT e.ebook_id, e.book_id
                    FROM ebooks e
                    WHERE e.ebook_id=%s
                    LIMIT 1
                    """,
                    (ebook_id,),
                )
                ebook = cur.fetchone()
                if not ebook:
                    return None

                cur.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM borrow_records
                    WHERE book_id=%s
                      AND return_date IS NULL
                      AND status IN ('active', 'borrowed', 'overdue')
                    """,
                    (ebook["book_id"],),
                )
                active_loans = int((cur.fetchone() or {}).get("count") or 0)

                cur.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM ebook_access_logs
                    WHERE ebook_id=%s
                      AND accessed_at >= (NOW() - INTERVAL 15 MINUTE)
                    """,
                    (ebook_id,),
                )
                recent_accesses = int((cur.fetchone() or {}).get("count") or 0)

                blockers = []
                if active_loans:
                    blockers.append(f"{active_loans} active loan(s) for the linked book")
                if recent_accesses:
                    blockers.append(f"{recent_accesses} recent e-book access event(s)")

                return blockers

    def delete_ebook(self, ebook_id: int):
        with get_connection() as conn:
            try:
                ensure_inventory_schema(conn)
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM ebooks WHERE ebook_id=%s LIMIT 1 FOR UPDATE", (ebook_id,))
                    ebook = cur.fetchone()
                    if not ebook:
                        return None

                    cur.execute(
                        """
                        DELETE FROM ebook_access_logs
                        WHERE ebook_id=%s
                          AND accessed_at < (NOW() - INTERVAL 15 MINUTE)
                        """,
                        (ebook_id,),
                    )
                    cur.execute("DELETE FROM ebooks WHERE ebook_id=%s", (ebook_id,))
                conn.commit()
                return ebook
            except Exception:
                conn.rollback()
                raise

    def log_ebook_access(self, ebook_id: int, actor_role: str, actor_id: int | None, action: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ebook_access_logs (ebook_id, actor_role, actor_id, action)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (ebook_id, actor_role, actor_id, action),
                )
                conn.commit()

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
                b.qr_code_path,
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
            GROUP BY b.book_id, b.isbn, b.title, b.qr_code_path, b.total_copies
            {having_clause}
            ORDER BY b.title ASC
        """

    def _book_count_query(self, where_clauses=None, having_clauses=None):
        select_query = self._book_select_query(where_clauses, having_clauses)
        return f"""
            SELECT COUNT(*) AS total
            FROM (
                {select_query}
            ) AS filtered_books
        """
