from datetime import datetime, timedelta

from ..database.db_connection import get_connection
from .inventory_schema import ensure_inventory_schema


ACTIVE_RESERVATION_STATUSES = ("active", "ready")


class ReservationRepositoryImpl:
    def ensure_schema(self, conn):
        ensure_inventory_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS reservations (
                    reservation_id INT PRIMARY KEY AUTO_INCREMENT,
                    student_id INT NOT NULL,
                    book_id INT NOT NULL,
                    ready_copy_id INT NULL,
                    queue_position INT NOT NULL DEFAULT 1,
                    reservation_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    status ENUM('active', 'ready', 'claimed', 'cancelled', 'expired') NOT NULL DEFAULT 'active',
                    expiration_date DATETIME NOT NULL,
                    approved_by INT NULL,
                    claimed_at DATETIME NULL,
                    cancelled_at DATETIME NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
                    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
                    FOREIGN KEY (ready_copy_id) REFERENCES book_copies(copy_id) ON DELETE SET NULL,
                    INDEX idx_student_status (student_id, status),
                    INDEX idx_book_queue (book_id, status, queue_position, reservation_date),
                    INDEX idx_expiration (status, expiration_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )

    def expire_reservations(self, conn=None):
        owns_connection = conn is None
        conn = conn or get_connection()
        try:
            self.ensure_schema(conn)
            expired_ready = []
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT reservation_id, book_id, ready_copy_id
                    FROM reservations
                    WHERE status IN ('active', 'ready')
                      AND expiration_date < NOW()
                    FOR UPDATE
                    """
                )
                expired = list(cur.fetchall() or [])
                for reservation in expired:
                    cur.execute(
                        """
                        UPDATE reservations
                        SET status='expired', queue_position=0, cancelled_at=NOW()
                        WHERE reservation_id=%s
                        """,
                        (reservation["reservation_id"],),
                    )
                    if reservation.get("ready_copy_id"):
                        expired_ready.append(reservation)

                for reservation in expired_ready:
                    self._advance_queue_for_copy(cur, reservation["book_id"], reservation["ready_copy_id"])

                touched_books = {row["book_id"] for row in expired}
                for book_id in touched_books:
                    self._resequence_queue(cur, book_id)

            if owns_connection:
                conn.commit()
            return len(expired)
        except Exception:
            if owns_connection:
                conn.rollback()
            raise
        finally:
            if owns_connection:
                conn.close()

    def create_reservation(self, student_id: int, book_id: int):
        with get_connection() as conn:
            try:
                self.ensure_schema(conn)
                self.expire_reservations(conn)
                with conn.cursor() as cur:
                    cur.execute("SELECT book_id, title FROM books WHERE book_id=%s LIMIT 1", (book_id,))
                    book = cur.fetchone()
                    if not book:
                        raise ValueError("Book not found.")

                    cur.execute(
                        """
                        SELECT borrow_id
                        FROM borrow_records
                        WHERE student_id=%s
                          AND book_id=%s
                          AND return_date IS NULL
                          AND status IN ('active', 'borrowed', 'overdue')
                        LIMIT 1
                        """,
                        (student_id, book_id),
                    )
                    if cur.fetchone():
                        raise ValueError("You already borrowed this book.")

                    cur.execute(
                        """
                        SELECT borrow_id
                        FROM borrow_records
                        WHERE student_id=%s
                          AND return_date IS NULL
                          AND status IN ('active', 'borrowed', 'overdue')
                          AND due_date < NOW()
                        LIMIT 1
                        """,
                        (student_id,),
                    )
                    if cur.fetchone():
                        raise ValueError("You cannot reserve books while you have overdue borrowed books.")

                    cur.execute(
                        """
                        SELECT fine_id
                        FROM fines
                        WHERE student_id=%s
                          AND status IN ('unpaid', 'pending')
                          AND amount > 0
                        LIMIT 1
                        """,
                        (student_id,),
                    )
                    if cur.fetchone():
                        raise ValueError("You cannot reserve books while you have unpaid fines.")

                    cur.execute(
                        """
                        SELECT reservation_id, status, queue_position, expiration_date
                        FROM reservations
                        WHERE student_id=%s
                          AND book_id=%s
                          AND status IN ('active', 'ready')
                        LIMIT 1
                        """,
                        (student_id, book_id),
                    )
                    existing = cur.fetchone()
                    if existing:
                        status = "ready for pickup" if existing["status"] == "ready" else "already reserved"
                        raise ValueError(f"This book is {status}. Your queue position is {existing['queue_position']}.")

                    cur.execute(
                        """
                        SELECT COALESCE(MAX(queue_position), 0) + 1 AS next_position
                        FROM reservations
                        WHERE book_id=%s
                          AND status IN ('active', 'ready')
                        FOR UPDATE
                        """,
                        (book_id,),
                    )
                    queue_position = int((cur.fetchone() or {}).get("next_position") or 1)
                    expiration_date = datetime.utcnow() + timedelta(days=7)
                    cur.execute(
                        """
                        INSERT INTO reservations
                            (student_id, book_id, queue_position, reservation_date, status, expiration_date)
                        VALUES (%s, %s, %s, NOW(), 'active', %s)
                        """,
                        (student_id, book_id, queue_position, expiration_date),
                    )
                    reservation_id = cur.lastrowid
                    if queue_position == 1:
                        copy_id = self._find_available_copy(cur, book_id)
                        if copy_id:
                            cur.execute("SELECT * FROM reservations WHERE reservation_id=%s", (reservation_id,))
                            self._mark_ready(cur, cur.fetchone(), copy_id)
                    cur.execute("SELECT * FROM reservations WHERE reservation_id=%s", (reservation_id,))
                    reservation = cur.fetchone()
                conn.commit()
                return reservation
            except Exception:
                conn.rollback()
                raise

    def list_student_reservations(self, student_id: int, limit: int | None = None, offset: int | None = None):
        with get_connection() as conn:
            self.ensure_schema(conn)
            self.expire_reservations(conn)
            conn.commit()
            with conn.cursor() as cur:
                params = [student_id]
                query = [
                    "SELECT r.*, b.title AS book_title, b.isbn,",
                    "       bc.copy_code, bc.barcode_value",
                    "FROM reservations r",
                    "JOIN books b ON r.book_id = b.book_id",
                    "LEFT JOIN book_copies bc ON r.ready_copy_id = bc.copy_id",
                    "WHERE r.student_id=%s",
                    "ORDER BY FIELD(r.status, 'ready', 'active', 'expired', 'cancelled', 'claimed'),",
                    "         r.reservation_date DESC"
                ]
                if limit is not None and offset is not None:
                    query[-1] += " LIMIT %s OFFSET %s"
                    params.extend([limit, offset])
                cur.execute(' '.join(query), tuple(params))
                rows = cur.fetchall()

        if limit is not None and offset is not None:
            with get_connection() as conn:
                self.ensure_schema(conn)
                self.expire_reservations(conn)
                conn.commit()
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(*) AS total FROM reservations WHERE student_id=%s",
                        (student_id,),
                    )
                    total = cur.fetchone().get('total', 0)
            return {
                'reservations': rows,
                'pagination': {
                    'page': (offset // limit) + 1,
                    'limit': limit,
                    'total': total,
                    'total_pages': max(1, (total + limit - 1) // limit)
                }
            }

        return rows

    def list_all_reservations(self, status=None, limit: int | None = None, offset: int | None = None):
        with get_connection() as conn:
            self.ensure_schema(conn)
            self.expire_reservations(conn)
            conn.commit()
            with conn.cursor() as cur:
                params = []
                status_filter = ""
                if status:
                    status_filter = "WHERE r.status=%s"
                    params.append(status)
                query = [
                    "SELECT r.*, b.title AS book_title, b.isbn,",
                    "       s.full_name AS student_name, s.email AS student_email, s.student_number,",
                    "       bc.copy_code, bc.barcode_value",
                    "FROM reservations r",
                    "JOIN books b ON r.book_id = b.book_id",
                    "JOIN students s ON r.student_id = s.student_id",
                    "LEFT JOIN book_copies bc ON r.ready_copy_id = bc.copy_id",
                    status_filter,
                    "ORDER BY FIELD(r.status, 'ready', 'active', 'expired', 'cancelled', 'claimed'),",
                    "         r.book_id ASC, r.queue_position ASC, r.reservation_date ASC"
                ]
                if limit is not None and offset is not None:
                    query[-1] += " LIMIT %s OFFSET %s"
                    params.extend([limit, offset])
                cur.execute(' '.join(query), tuple(params))
                rows = cur.fetchall()

        if limit is not None and offset is not None:
            with get_connection() as conn:
                self.ensure_schema(conn)
                self.expire_reservations(conn)
                conn.commit()
                with conn.cursor() as cur:
                    count_query = "SELECT COUNT(*) AS total FROM reservations r "
                    if status_filter:
                        count_query += status_filter
                    cur.execute(count_query, tuple(params[:len(params) - 2] if limit is not None and offset is not None else tuple(params)))
                    total = cur.fetchone().get('total', 0)
            return {
                'reservations': rows,
                'pagination': {
                    'page': (offset // limit) + 1,
                    'limit': limit,
                    'total': total,
                    'total_pages': max(1, (total + limit - 1) // limit)
                }
            }

        return rows

    def cancel_reservation(self, reservation_id: int, student_id=None):
        with get_connection() as conn:
            try:
                self.ensure_schema(conn)
                with conn.cursor() as cur:
                    student_filter = "AND student_id=%s" if student_id is not None else ""
                    params = [reservation_id]
                    if student_id is not None:
                        params.append(student_id)
                    cur.execute(
                        f"""
                        SELECT *
                        FROM reservations
                        WHERE reservation_id=%s
                          {student_filter}
                          AND status IN ('active', 'ready')
                        LIMIT 1
                        FOR UPDATE
                        """,
                        tuple(params),
                    )
                    reservation = cur.fetchone()
                    if not reservation:
                        conn.rollback()
                        return None

                    cur.execute(
                        """
                        UPDATE reservations
                        SET status='cancelled', queue_position=0, cancelled_at=NOW()
                        WHERE reservation_id=%s
                        """,
                        (reservation_id,),
                    )
                    if reservation.get("ready_copy_id"):
                        self._advance_queue_for_copy(cur, reservation["book_id"], reservation["ready_copy_id"])
                    self._resequence_queue(cur, reservation["book_id"])
                conn.commit()
                return reservation
            except Exception:
                conn.rollback()
                raise

    def approve_reservation(self, reservation_id: int, actor_id=None):
        with get_connection() as conn:
            try:
                self.ensure_schema(conn)
                self.expire_reservations(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT *
                        FROM reservations
                        WHERE reservation_id=%s
                          AND status='active'
                        LIMIT 1
                        FOR UPDATE
                        """,
                        (reservation_id,),
                    )
                    reservation = cur.fetchone()
                    if not reservation:
                        conn.rollback()
                        return None

                    copy_id = self._find_available_copy(cur, reservation["book_id"])
                    if not copy_id:
                        cur.execute(
                            "UPDATE reservations SET approved_by=%s WHERE reservation_id=%s",
                            (actor_id, reservation_id),
                        )
                        conn.commit()
                        reservation["message"] = "Reservation remains queued until a copy is returned."
                        return reservation

                    self._mark_ready(cur, reservation, copy_id, actor_id)
                    cur.execute("SELECT * FROM reservations WHERE reservation_id=%s", (reservation_id,))
                    updated = cur.fetchone()
                conn.commit()
                return updated
            except Exception:
                conn.rollback()
                raise

    def mark_claimed(self, reservation_id: int, actor_id=None):
        with get_connection() as conn:
            try:
                self.ensure_schema(conn)
                self.expire_reservations(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT *
                        FROM reservations
                        WHERE reservation_id=%s
                          AND status='ready'
                        LIMIT 1
                        FOR UPDATE
                        """,
                        (reservation_id,),
                    )
                    reservation = cur.fetchone()
                    if not reservation:
                        conn.rollback()
                        return None
                    if not reservation.get("ready_copy_id"):
                        raise ValueError("Reservation has no assigned copy.")

                    due_date = datetime.utcnow() + timedelta(days=14)
                    cur.execute(
                        """
                        INSERT INTO borrow_records
                            (student_id, book_id, copy_id, borrow_date, due_date, status)
                        VALUES (%s, %s, %s, NOW(), %s, 'active')
                        """,
                        (reservation["student_id"], reservation["book_id"], reservation["ready_copy_id"], due_date),
                    )
                    loan_id = cur.lastrowid
                    cur.execute(
                        "UPDATE book_copies SET status='borrowed' WHERE copy_id=%s",
                        (reservation["ready_copy_id"],),
                    )
                    cur.execute(
                        """
                        UPDATE reservations
                        SET status='claimed', queue_position=0, claimed_at=NOW(), approved_by=COALESCE(approved_by, %s)
                        WHERE reservation_id=%s
                        """,
                        (actor_id, reservation_id),
                    )
                    self._resequence_queue(cur, reservation["book_id"])
                conn.commit()
                return {"reservation_id": reservation_id, "loan_id": loan_id}
            except Exception:
                conn.rollback()
                raise

    def assign_next_on_return(self, conn, book_id: int, copy_id: int, actor_id=None):
        self.ensure_schema(conn)
        self.expire_reservations(conn)
        with conn.cursor() as cur:
            assigned = self._advance_queue_for_copy(cur, book_id, copy_id, actor_id)
            if not assigned:
                cur.execute("UPDATE book_copies SET status='available' WHERE copy_id=%s", (copy_id,))
            self._resequence_queue(cur, book_id)
            return assigned

    def _find_available_copy(self, cur, book_id: int):
        cur.execute(
            """
            SELECT copy_id
            FROM book_copies
            WHERE book_id=%s
              AND status='available'
            ORDER BY copy_id
            LIMIT 1
            FOR UPDATE
            """,
            (book_id,),
        )
        row = cur.fetchone()
        return row["copy_id"] if row else None

    def _advance_queue_for_copy(self, cur, book_id: int, copy_id: int, actor_id=None):
        cur.execute(
            """
            SELECT *
            FROM reservations
            WHERE book_id=%s
              AND status='active'
            ORDER BY queue_position ASC, reservation_date ASC, reservation_id ASC
            LIMIT 1
            FOR UPDATE
            """,
            (book_id,),
        )
        reservation = cur.fetchone()
        if not reservation:
            cur.execute("UPDATE book_copies SET status='available' WHERE copy_id=%s", (copy_id,))
            return None
        self._mark_ready(cur, reservation, copy_id, actor_id)
        reservation["ready_copy_id"] = copy_id
        reservation["status"] = "ready"
        reservation["expiration_date"] = datetime.utcnow() + timedelta(days=2)
        return reservation

    def _mark_ready(self, cur, reservation, copy_id: int, actor_id=None):
        cur.execute("UPDATE book_copies SET status='reserved' WHERE copy_id=%s", (copy_id,))
        cur.execute(
            """
            UPDATE reservations
            SET status='ready',
                ready_copy_id=%s,
                queue_position=1,
                expiration_date=%s,
                approved_by=COALESCE(%s, approved_by)
            WHERE reservation_id=%s
            """,
            (copy_id, datetime.utcnow() + timedelta(days=2), actor_id, reservation["reservation_id"]),
        )

    def _resequence_queue(self, cur, book_id: int):
        cur.execute(
            """
            SELECT reservation_id
            FROM reservations
            WHERE book_id=%s
              AND status IN ('ready', 'active')
            ORDER BY FIELD(status, 'ready', 'active'), reservation_date ASC, reservation_id ASC
            """,
            (book_id,),
        )
        for position, row in enumerate(cur.fetchall() or [], start=1):
            cur.execute(
                "UPDATE reservations SET queue_position=%s WHERE reservation_id=%s",
                (position, row["reservation_id"]),
            )
