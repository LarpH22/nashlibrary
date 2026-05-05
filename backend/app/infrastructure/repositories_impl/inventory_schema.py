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
                barcode_value VARCHAR(80) UNIQUE,
                qr_token VARCHAR(120) UNIQUE,
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

        _ensure_book_copy_metadata_columns(cur)
        _ensure_ebook_tables(cur)
        _ensure_ebook_metadata_columns(cur)
        _ensure_qr_code_columns(cur)

        if not _column_exists(cur, "borrow_records", "copy_id"):
            cur.execute("ALTER TABLE borrow_records ADD COLUMN copy_id INT NULL AFTER book_id")

        if not _index_exists(cur, "borrow_records", "idx_copy_id"):
            cur.execute("ALTER TABLE borrow_records ADD INDEX idx_copy_id (copy_id)")

        _ensure_book_copy_rows(cur)
        _backfill_copy_scan_metadata(cur)
        _assign_existing_active_loans(cur)
        _reconcile_copy_statuses(cur)


def _ensure_book_copy_metadata_columns(cur):
    if not _column_exists(cur, "book_copies", "barcode_value"):
        cur.execute("ALTER TABLE book_copies ADD COLUMN barcode_value VARCHAR(80) UNIQUE AFTER copy_code")
    if not _column_exists(cur, "book_copies", "qr_token"):
        cur.execute("ALTER TABLE book_copies ADD COLUMN qr_token VARCHAR(120) UNIQUE AFTER barcode_value")

    if not _index_exists(cur, "book_copies", "idx_barcode_value"):
        cur.execute("ALTER TABLE book_copies ADD INDEX idx_barcode_value (barcode_value)")
    if not _index_exists(cur, "book_copies", "idx_qr_token"):
        cur.execute("ALTER TABLE book_copies ADD INDEX idx_qr_token (qr_token)")


def _ensure_ebook_tables(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ebooks (
            ebook_id INT PRIMARY KEY AUTO_INCREMENT,
            book_id INT NULL,
            title VARCHAR(255) NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            stored_filename VARCHAR(255) NOT NULL UNIQUE,
            file_path VARCHAR(500) NOT NULL,
            file_type ENUM('pdf', 'epub') NOT NULL,
            file_size BIGINT NOT NULL DEFAULT 0,
            access_level ENUM('students', 'librarians', 'admins') NOT NULL DEFAULT 'students',
            uploaded_by_role ENUM('admin', 'librarian') NOT NULL,
            uploaded_by_id INT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE SET NULL,
            INDEX idx_book_id (book_id),
            INDEX idx_access_level (access_level)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    )

    if _column_exists(cur, "ebooks", "book_id"):
        cur.execute("ALTER TABLE ebooks MODIFY COLUMN book_id INT NULL")

    if not _index_exists(cur, "ebooks", "idx_book_id"):
        cur.execute("ALTER TABLE ebooks ADD INDEX idx_book_id (book_id)")

    if not _index_exists(cur, "ebooks", "idx_access_level"):
        cur.execute("ALTER TABLE ebooks ADD INDEX idx_access_level (access_level)")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ebook_access_logs (
            access_id INT PRIMARY KEY AUTO_INCREMENT,
            ebook_id INT NOT NULL,
            actor_role ENUM('student', 'librarian', 'admin') NOT NULL,
            actor_id INT,
            action ENUM('view', 'download') NOT NULL DEFAULT 'view',
            accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ebook_id) REFERENCES ebooks(ebook_id) ON DELETE CASCADE,
            INDEX idx_ebook_id (ebook_id),
            INDEX idx_actor (actor_role, actor_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS loan_reminders (
            reminder_id INT PRIMARY KEY AUTO_INCREMENT,
            borrow_id INT NOT NULL,
            reminder_type ENUM('due_soon', 'overdue') NOT NULL,
            sent_to VARCHAR(255) NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status ENUM('sent', 'failed') NOT NULL DEFAULT 'sent',
            error_message TEXT,
            FOREIGN KEY (borrow_id) REFERENCES borrow_records(borrow_id) ON DELETE CASCADE,
            INDEX idx_borrow_type (borrow_id, reminder_type),
            INDEX idx_sent_at (sent_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    )


def _ensure_ebook_metadata_columns(cur):
    if not _column_exists(cur, "ebooks", "author"):
        cur.execute("ALTER TABLE ebooks ADD COLUMN author VARCHAR(255) NULL AFTER title")
    if not _column_exists(cur, "ebooks", "category"):
        cur.execute("ALTER TABLE ebooks ADD COLUMN category VARCHAR(255) NULL AFTER author")


def _ensure_qr_code_columns(cur):
    if not _column_exists(cur, "books", "qr_code_path"):
        cur.execute("ALTER TABLE books ADD COLUMN qr_code_path VARCHAR(500) NULL")
    if not _column_exists(cur, "ebooks", "qr_code_path"):
        cur.execute("ALTER TABLE ebooks ADD COLUMN qr_code_path VARCHAR(500) NULL")


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


def _backfill_copy_scan_metadata(cur):
    cur.execute(
        """
        SELECT copy_id, copy_code, barcode_value, qr_token
        FROM book_copies
        WHERE barcode_value IS NULL OR barcode_value = '' OR qr_token IS NULL OR qr_token = ''
        ORDER BY copy_id
        """
    )
    for copy in cur.fetchall():
        barcode_value = copy.get("barcode_value") or copy.get("copy_code") or f"COPY-{copy['copy_id']}"
        qr_token = copy.get("qr_token") or f"QR-{copy['copy_id']}-{barcode_value}"
        cur.execute(
            """
            UPDATE book_copies
            SET barcode_value=%s, qr_token=%s
            WHERE copy_id=%s
            """,
            (barcode_value, qr_token[:120], copy["copy_id"]),
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
        INSERT INTO book_copies (book_id, copy_code, barcode_value, qr_token, status)
        VALUES (%s, %s, %s, %s, 'borrowed')
        """,
        (
            book_id,
            _copy_code({**book, "book_id": book_id}, sequence),
            _copy_code({**book, "book_id": book_id}, sequence),
            f"QR-MIGRATED-{book_id}-{sequence:03d}",
        ),
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
