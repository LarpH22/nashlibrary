ACTIVE_LOAN_STATUSES = ("active", "borrowed", "overdue")


def ensure_inventory_schema(conn):
    """Ensure copy-level inventory exists for borrow/return operations."""
    with conn.cursor() as cur:
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

        if not _column_exists(cur, "borrow_records", "copy_id"):
            cur.execute("ALTER TABLE borrow_records ADD COLUMN copy_id INT NULL AFTER book_id")

        if not _index_exists(cur, "borrow_records", "idx_copy_id"):
            cur.execute("ALTER TABLE borrow_records ADD INDEX idx_copy_id (copy_id)")

        _ensure_book_copy_rows(cur)
        _assign_existing_active_loans(cur)
        _reconcile_copy_statuses(cur)


def _column_exists(cur, table_name, column_name):
    cur.execute(
        """
        SELECT COUNT(*) AS count
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = %s
          AND column_name = %s
        """,
        (table_name, column_name),
    )
    return cur.fetchone()["count"] > 0


def _index_exists(cur, table_name, index_name):
    cur.execute(
        """
        SELECT COUNT(*) AS count
        FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name = %s
          AND index_name = %s
        """,
        (table_name, index_name),
    )
    return cur.fetchone()["count"] > 0


def _ensure_book_copy_rows(cur):
    cur.execute(
        """
        SELECT b.book_id, b.isbn, b.total_copies, COUNT(bc.copy_id) AS copy_count
        FROM books b
        LEFT JOIN book_copies bc ON b.book_id = bc.book_id
        GROUP BY b.book_id, b.isbn, b.total_copies
        """
    )
    for book in cur.fetchall():
        total_copies = max(int(book.get("total_copies") or 1), 1)
        copy_count = int(book.get("copy_count") or 0)
        for sequence in range(copy_count + 1, total_copies + 1):
            cur.execute(
                """
                INSERT IGNORE INTO book_copies (book_id, copy_code, status)
                VALUES (%s, %s, 'available')
                """,
                (book["book_id"], _copy_code(book, sequence)),
            )


def _assign_existing_active_loans(cur):
    cur.execute(
        """
        SELECT borrow_id, book_id
        FROM borrow_records
        WHERE copy_id IS NULL
          AND return_date IS NULL
          AND status IN ('active', 'borrowed', 'overdue')
        ORDER BY borrow_id
        FOR UPDATE
        """
    )
    for loan in cur.fetchall():
        copy_id = _find_unassigned_copy(cur, loan["book_id"])
        if copy_id is None:
            copy_id = _create_migrated_copy(cur, loan["book_id"])
        cur.execute(
            "UPDATE borrow_records SET copy_id=%s WHERE borrow_id=%s",
            (copy_id, loan["borrow_id"]),
        )
        cur.execute(
            "UPDATE book_copies SET status='borrowed' WHERE copy_id=%s",
            (copy_id,),
        )


def _find_unassigned_copy(cur, book_id):
    cur.execute(
        """
        SELECT bc.copy_id
        FROM book_copies bc
        LEFT JOIN borrow_records br
          ON br.copy_id = bc.copy_id
         AND br.return_date IS NULL
         AND br.status IN ('active', 'borrowed', 'overdue')
        WHERE bc.book_id = %s
          AND br.borrow_id IS NULL
        ORDER BY FIELD(bc.status, 'available', 'borrowed', 'maintenance', 'lost'), bc.copy_id
        LIMIT 1
        FOR UPDATE
        """,
        (book_id,),
    )
    row = cur.fetchone()
    return row["copy_id"] if row else None


def _create_migrated_copy(cur, book_id):
    cur.execute("SELECT isbn FROM books WHERE book_id=%s LIMIT 1", (book_id,))
    book = cur.fetchone() or {"book_id": book_id, "isbn": None}
    cur.execute("SELECT COUNT(*) AS count FROM book_copies WHERE book_id=%s", (book_id,))
    sequence = int(cur.fetchone()["count"] or 0) + 1
    cur.execute(
        """
        INSERT INTO book_copies (book_id, copy_code, status)
        VALUES (%s, %s, 'borrowed')
        """,
        (book_id, _copy_code({**book, "book_id": book_id}, sequence)),
    )
    return cur.lastrowid


def _reconcile_copy_statuses(cur):
    cur.execute(
        """
        UPDATE book_copies bc
        JOIN borrow_records br ON br.copy_id = bc.copy_id
        SET bc.status = 'borrowed'
        WHERE br.return_date IS NULL
          AND br.status IN ('active', 'borrowed', 'overdue')
        """
    )


def _copy_code(book, sequence):
    base = book.get("isbn") or f"BOOK-{book['book_id']}"
    return f"{base}-{sequence:03d}"
