import logging
from datetime import datetime, date

from ..database.db_connection import get_connection
from ...domain.repositories.loan_repository import LoanRepository
from .inventory_schema import ACTIVE_LOAN_STATUSES, ensure_inventory_schema

FINE_RATE_PER_DAY = 1.0

logger = logging.getLogger(__name__)


class LoanRepositoryImpl(LoanRepository):
    def create_loan_for_copy(self, copy_id: int, user_id: int, borrowed_at, due_date):
        with get_connection() as conn:
            try:
                ensure_inventory_schema(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT copy_id, book_id, status
                        FROM book_copies
                        WHERE copy_id=%s
                        LIMIT 1
                        FOR UPDATE
                        """,
                        (copy_id,),
                    )
                    copy = cur.fetchone()
                    if not copy:
                        raise ValueError('Book copy not found')
                    if copy.get('status') != 'available':
                        raise ValueError('Book copy is not available')

                    cur.execute(
                        """
                        SELECT borrow_id
                        FROM borrow_records
                        WHERE copy_id=%s
                          AND return_date IS NULL
                          AND status IN ('active', 'borrowed', 'overdue')
                        LIMIT 1
                        FOR UPDATE
                        """,
                        (copy_id,),
                    )
                    if cur.fetchone():
                        raise ValueError('This book copy is already borrowed')

                    cur.execute(
                        """
                        INSERT INTO borrow_records
                            (student_id, book_id, copy_id, borrow_date, due_date, status)
                        VALUES (%s, %s, %s, %s, %s, 'active')
                        """,
                        (user_id, copy['book_id'], copy_id, borrowed_at, due_date),
                    )
                    loan_id = cur.lastrowid
                    cur.execute(
                        "UPDATE book_copies SET status='borrowed' WHERE copy_id=%s AND status='available'",
                        (copy_id,),
                    )
                    if cur.rowcount == 0:
                        raise ValueError('Book copy is not available')
                conn.commit()
                return loan_id
            except Exception:
                conn.rollback()
                raise

    def _ensure_borrow_request_schema(self, conn):
        ensure_inventory_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS borrow_requests (
                    request_id INT PRIMARY KEY AUTO_INCREMENT,
                    student_id INT NOT NULL,
                    book_id INT NOT NULL,
                    copy_id INT NULL,
                    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
                    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    decided_at TIMESTAMP NULL,
                    approved_by INT NULL,
                    due_date DATE NULL,
                    borrow_id INT NULL,
                    rejection_reason VARCHAR(255) NULL,
                    INDEX idx_student_status (student_id, status),
                    INDEX idx_book_status (book_id, status),
                    INDEX idx_copy_status (copy_id, status)
                )
                """
            )

    def create_borrow_request(self, book_id: int, student_id: int):
        with get_connection() as conn:
            try:
                self._ensure_borrow_request_schema(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT book_id
                        FROM books
                        WHERE book_id=%s
                        LIMIT 1
                        """,
                        (book_id,),
                    )
                    if not cur.fetchone():
                        raise ValueError('Book not found')

                    cur.execute(
                        """
                        SELECT request_id
                        FROM borrow_requests
                        WHERE student_id=%s
                          AND book_id=%s
                          AND status='pending'
                        LIMIT 1
                        """,
                        (student_id, book_id),
                    )
                    if cur.fetchone():
                        raise ValueError('You already have a pending request for this book')

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
                        raise ValueError('You already have an active loan for this book')

                    cur.execute(
                        """
                        INSERT INTO borrow_requests (student_id, book_id, status, requested_at)
                        VALUES (%s, %s, 'pending', NOW())
                        """,
                        (student_id, book_id),
                    )
                    request_id = cur.lastrowid
                conn.commit()
                return request_id
            except Exception:
                conn.rollback()
                raise

    def list_borrow_requests(self, status: str | None = None):
        with get_connection() as conn:
            self._ensure_borrow_request_schema(conn)
            conn.commit()
            with conn.cursor() as cur:
                where = ''
                params = []
                if status:
                    where = 'WHERE brq.status=%s'
                    params.append(status)
                cur.execute(
                    f"""
                    SELECT
                        brq.request_id,
                        brq.student_id,
                        s.full_name AS student_name,
                        s.email AS student_email,
                        s.student_number,
                        brq.book_id,
                        b.title AS book_title,
                        brq.copy_id,
                        bc.copy_code,
                        brq.status,
                        brq.requested_at,
                        brq.decided_at,
                        brq.due_date,
                        brq.borrow_id,
                        brq.rejection_reason
                    FROM borrow_requests brq
                    LEFT JOIN students s ON brq.student_id = s.student_id
                    LEFT JOIN books b ON brq.book_id = b.book_id
                    LEFT JOIN book_copies bc ON brq.copy_id = bc.copy_id
                    {where}
                    ORDER BY brq.requested_at DESC
                    """,
                    tuple(params),
                )
                requests = cur.fetchall()
                for request in requests:
                    self._convert_dates(request, ['requested_at', 'decided_at', 'due_date'])
                return requests

    def approve_borrow_request(self, request_id: int, due_date, approved_by: int | None = None):
        if not due_date:
            raise ValueError('Due date is required')

        if isinstance(due_date, str):
            try:
                due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            except ValueError as exc:
                raise ValueError('Due date must use YYYY-MM-DD format') from exc
        elif isinstance(due_date, datetime):
            due_date = due_date.date()

        today = datetime.utcnow().date()
        if due_date < today:
            raise ValueError('Due date cannot be in the past')

        with get_connection() as conn:
            try:
                self._ensure_borrow_request_schema(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT *
                        FROM borrow_requests
                        WHERE request_id=%s AND status='pending'
                        LIMIT 1
                        FOR UPDATE
                        """,
                        (request_id,),
                    )
                    request = cur.fetchone()
                    if not request:
                        conn.rollback()
                        return None

                    cur.execute(
                        """
                        SELECT copy_id
                        FROM book_copies
                        WHERE book_id=%s AND status='available'
                        ORDER BY copy_id
                        LIMIT 1
                        FOR UPDATE
                        """,
                        (request['book_id'],),
                    )
                    copy = cur.fetchone()
                    if not copy:
                        raise ValueError('No available copy remains for this request')

                    cur.execute(
                        """
                        INSERT INTO borrow_records
                            (student_id, book_id, copy_id, borrow_date, due_date, status)
                        VALUES (%s, %s, %s, %s, %s, 'active')
                        """,
                        (request['student_id'], request['book_id'], copy['copy_id'], today, due_date),
                    )
                    borrow_id = cur.lastrowid

                    cur.execute(
                        "UPDATE book_copies SET status='borrowed' WHERE copy_id=%s AND status='available'",
                        (copy['copy_id'],),
                    )
                    if cur.rowcount == 0:
                        raise ValueError('Book copy is not available')

                    cur.execute(
                        """
                        UPDATE borrow_requests
                        SET status='approved',
                            copy_id=%s,
                            borrow_id=%s,
                            due_date=%s,
                            approved_by=%s,
                            decided_at=NOW()
                        WHERE request_id=%s
                        """,
                        (copy['copy_id'], borrow_id, due_date, approved_by, request_id),
                    )
                conn.commit()
                return borrow_id
            except Exception:
                conn.rollback()
                raise

    def reject_borrow_request(self, request_id: int, reason: str | None = None):
        with get_connection() as conn:
            try:
                self._ensure_borrow_request_schema(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE borrow_requests
                        SET status='rejected',
                            rejection_reason=%s,
                            decided_at=NOW()
                        WHERE request_id=%s AND status='pending'
                        """,
                        (reason, request_id),
                    )
                    updated = cur.rowcount
                conn.commit()
                return updated > 0
            except Exception:
                conn.rollback()
                raise

    def create_loan(self, book_id: int, user_id: int, borrowed_at, due_date):
        with get_connection() as conn:
            try:
                ensure_inventory_schema(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT copy_id, status
                        FROM book_copies
                        WHERE book_id=%s
                          AND status='available'
                        ORDER BY copy_id
                        LIMIT 1
                        FOR UPDATE
                        """,
                        (book_id,),
                    )
                    copy = cur.fetchone()
                    if not copy:
                        raise ValueError('Book copy is not available')

                    cur.execute(
                        """
                        SELECT borrow_id
                        FROM borrow_records
                        WHERE copy_id=%s
                          AND return_date IS NULL
                          AND status IN ('active', 'borrowed', 'overdue')
                        LIMIT 1
                        FOR UPDATE
                        """,
                        (copy['copy_id'],),
                    )
                    if cur.fetchone():
                        raise ValueError('This book copy is already borrowed')

                    cur.execute(
                        """
                        INSERT INTO borrow_records
                            (student_id, book_id, copy_id, borrow_date, due_date, status)
                        VALUES (%s, %s, %s, %s, %s, 'active')
                        """,
                        (user_id, book_id, copy['copy_id'], borrowed_at, due_date),
                    )
                    loan_id = cur.lastrowid
                    cur.execute(
                        "UPDATE book_copies SET status='borrowed' WHERE copy_id=%s AND status='available'",
                        (copy['copy_id'],),
                    )
                    if cur.rowcount == 0:
                        raise ValueError('Book copy is not available')
                conn.commit()
                return loan_id
            except Exception:
                conn.rollback()
                raise

    def close_loan_by_copy_code(self, scan_code: str, returned_at, student_id: int | None = None):
        with get_connection() as conn:
            ensure_inventory_schema(conn)
            conn.commit()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT br.borrow_id
                    FROM book_copies bc
                    JOIN borrow_records br ON br.copy_id = bc.copy_id
                    WHERE (bc.copy_code=%s OR bc.barcode_value=%s OR bc.qr_token=%s)
                      AND br.return_date IS NULL
                      AND br.status IN ('active', 'borrowed', 'overdue')
                      {student_filter}
                    ORDER BY br.borrow_id DESC
                    LIMIT 1
                    """.format(student_filter="AND br.student_id=%s" if student_id is not None else ""),
                    (scan_code, scan_code, scan_code, student_id) if student_id is not None else (scan_code, scan_code, scan_code),
                )
                row = cur.fetchone()
        if not row:
            return None
        return self.close_loan(row['borrow_id'], returned_at, student_id)

    def close_loan(self, loan_id: int, returned_at, student_id: int | None = None):
        with get_connection() as conn:
            try:
                ensure_inventory_schema(conn)
                with conn.cursor() as cur:
                    status_placeholders = ', '.join(['%s'] * len(ACTIVE_LOAN_STATUSES))
                    params = [loan_id]
                    student_filter = ''
                    if student_id is not None:
                        student_filter = 'AND student_id=%s'
                        params.append(student_id)
                    params.extend(ACTIVE_LOAN_STATUSES)
                    cur.execute(
                        f"""
                        SELECT *
                        FROM borrow_records
                        WHERE borrow_id=%s
                          {student_filter}
                          AND return_date IS NULL
                          AND status IN ({status_placeholders})
                        LIMIT 1
                        FOR UPDATE
                        """,
                        tuple(params),
                    )
                    loan = cur.fetchone()
                    if not loan:
                        conn.rollback()
                        return None

                    cur.execute(
                        "UPDATE borrow_records SET return_date=%s, status='returned' WHERE borrow_id=%s",
                        (returned_at, loan_id),
                    )
                    if loan.get('copy_id'):
                        cur.execute(
                            "UPDATE book_copies SET status='available' WHERE copy_id=%s",
                            (loan['copy_id'],),
                        )

                    due_date = loan.get('due_date')
                    fine_amount = self._compute_fine(due_date, returned_at)
                    if fine_amount > 0 and loan.get('student_id'):
                        issued_date = returned_at.date() if isinstance(returned_at, datetime) else returned_at
                        cur.execute("SELECT 1 FROM fines WHERE borrow_id=%s LIMIT 1", (loan_id,))
                        if not cur.fetchone():
                            cur.execute(
                                """
                                INSERT INTO fines (borrow_id, student_id, amount, reason, status, issued_date)
                                VALUES (%s, %s, %s, %s, 'unpaid', %s)
                                """,
                                (loan_id, loan['student_id'], fine_amount, 'Overdue book return', issued_date),
                            )

                    conn.commit()
                    cur.execute("SELECT * FROM borrow_records WHERE borrow_id=%s", (loan_id,))
                    returned_loan = cur.fetchone()
                    if returned_loan:
                        returned_loan['fine_amount'] = fine_amount
                        returned_loan['days_overdue'] = self._compute_days_overdue(due_date, returned_at)
                    return returned_loan
            except Exception:
                conn.rollback()
                raise

    def find_active_loan(self, book_id: int, user_id: int):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM borrow_records
                    WHERE book_id=%s
                      AND student_id=%s
                      AND return_date IS NULL
                      AND status IN ('active', 'borrowed', 'overdue')
                    LIMIT 1
                    """,
                    (book_id, user_id),
                )
                return cur.fetchone()

    def find_loan_by_id(self, loan_id: int):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        br.borrow_id AS loan_id,
                        br.student_id,
                        br.book_id,
                        br.copy_id,
                        bc.copy_code,
                        b.title AS book_title,
                        br.borrow_date AS issue_date,
                        br.due_date,
                        br.return_date,
                        br.status
                    FROM borrow_records br
                    LEFT JOIN books b ON br.book_id = b.book_id
                    LEFT JOIN book_copies bc ON br.copy_id = bc.copy_id
                    WHERE br.borrow_id=%s
                    LIMIT 1
                    """,
                    (loan_id,),
                )
                loan = cur.fetchone()
                if loan:
                    self._convert_dates(loan, ['issue_date', 'due_date', 'return_date'])
                return loan

    def find_loans_by_student_id(self, student_id: int):
        try:
            with get_connection() as conn:
                self._ensure_borrow_request_schema(conn)
                conn.commit()
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                            br.borrow_id AS loan_id,
                            br.student_id,
                            br.book_id,
                            br.copy_id,
                            bc.copy_code,
                            b.title AS book_title,
                            GROUP_CONCAT(DISTINCT a.name ORDER BY ba.author_order SEPARATOR ', ') as authors,
                            b.isbn,
                            b.publisher AS book_publisher,
                            b.publication_year,
                            br.borrow_date AS issue_date,
                            br.due_date,
                            br.return_date,
                            br.status,
                            CASE WHEN br.status = 'returned' THEN TRUE ELSE FALSE END AS returned
                        FROM borrow_records br
                        LEFT JOIN books b ON br.book_id = b.book_id
                        LEFT JOIN book_copies bc ON br.copy_id = bc.copy_id
                        LEFT JOIN book_authors ba ON b.book_id = ba.book_id
                        LEFT JOIN authors a ON ba.author_id = a.author_id
                        WHERE br.student_id = %s
                        GROUP BY br.borrow_id, br.student_id, br.book_id, br.copy_id, bc.copy_code, b.title, b.isbn, b.publisher, b.publication_year, br.borrow_date, br.due_date, br.return_date, br.status
                        ORDER BY br.borrow_date DESC
                        """,
                        (student_id,)
                    )
                    loans = list(cur.fetchall() or [])

                    # Convert all date/datetime objects to ISO format strings for JSON serialization
                    if loans:
                        for loan in loans:
                            due_date = loan.get('due_date')
                            return_date = loan.get('return_date')
                            loan['fine_amount'] = self._get_outstanding_fine(
                                cur,
                                loan['loan_id'],
                                due_date,
                                return_date or datetime.utcnow(),
                            )
                            loan['days_overdue'] = self._compute_days_overdue(due_date, return_date or datetime.utcnow())

                            for field_name in ['issue_date', 'due_date', 'return_date']:
                                self._convert_dates(loan, [field_name])

                    cur.execute(
                        """
                        SELECT
                            brq.request_id,
                            brq.student_id,
                            brq.book_id,
                            b.title AS book_title,
                            brq.status,
                            brq.requested_at,
                            brq.decided_at,
                            brq.due_date,
                            brq.rejection_reason
                        FROM borrow_requests brq
                        LEFT JOIN books b ON brq.book_id = b.book_id
                        WHERE brq.student_id=%s
                          AND brq.status IN ('pending', 'rejected')
                        ORDER BY brq.requested_at DESC
                        """,
                        (student_id,),
                    )
                    requests = list(cur.fetchall() or [])
                    for request in requests:
                        request['loan_id'] = f"request-{request['request_id']}"
                        request['issue_date'] = request.get('requested_at')
                        request['return_date'] = None
                        request['returned'] = False
                        request['fine_amount'] = 0.0
                        request['days_overdue'] = 0
                        request['is_request'] = True
                        self._convert_dates(request, ['requested_at', 'decided_at', 'due_date', 'issue_date'])

                    return requests + loans
        except Exception as exc:
            logger.exception('Failed to query loans for student_id=%r', student_id)
            raise

    def _convert_dates(self, row, fields):
        for field in fields:
            if field in row and row[field] is not None and hasattr(row[field], 'isoformat'):
                row[field] = row[field].isoformat()

    def find_fines_by_student_id(self, student_id: int):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        f.fine_id,
                        f.borrow_id AS loan_id,
                        f.borrow_id,
                        f.student_id,
                        f.amount,
                        f.reason,
                        f.status,
                        f.issued_date,
                        f.paid_date,
                        br.book_id,
                        br.copy_id,
                        bc.copy_code,
                        b.title AS book_title,
                        br.borrow_date AS issue_date,
                        br.due_date,
                        br.return_date,
                        br.status AS loan_status
                    FROM fines f
                    LEFT JOIN borrow_records br ON f.borrow_id = br.borrow_id
                    LEFT JOIN books b ON br.book_id = b.book_id
                    LEFT JOIN book_copies bc ON br.copy_id = bc.copy_id
                    WHERE f.student_id=%s
                    ORDER BY f.issued_date DESC, f.fine_id DESC
                    """,
                    (student_id,),
                )
                fines = list(cur.fetchall() or [])
                seen_loan_ids = set()
                for fine in fines:
                    seen_loan_ids.add(fine.get('loan_id'))
                    amount = fine.get('amount')
                    fine['amount'] = round(float(amount or 0), 2)
                    fine['fine_amount'] = fine['amount']
                    fine['days_overdue'] = self._compute_days_overdue(
                        fine.get('due_date'),
                        fine.get('return_date') or fine.get('paid_date') or datetime.utcnow(),
                    )
                    fine['is_paid'] = fine.get('status') == 'paid'
                    fine['is_unpaid'] = fine.get('status') in ('unpaid', 'pending')
                    fine['source'] = 'recorded'
                    self._convert_dates(fine, ['issued_date', 'paid_date', 'issue_date', 'due_date', 'return_date'])

                cur.execute(
                    """
                    SELECT
                        br.borrow_id AS loan_id,
                        br.borrow_id,
                        br.student_id,
                        br.book_id,
                        br.copy_id,
                        bc.copy_code,
                        b.title AS book_title,
                        br.borrow_date AS issue_date,
                        br.due_date,
                        br.return_date,
                        br.status AS loan_status
                    FROM borrow_records br
                    LEFT JOIN books b ON br.book_id = b.book_id
                    LEFT JOIN book_copies bc ON br.copy_id = bc.copy_id
                    WHERE br.student_id=%s
                      AND br.due_date IS NOT NULL
                      AND DATE(br.due_date) < CURDATE()
                      AND br.borrow_id NOT IN (
                          SELECT borrow_id FROM fines WHERE student_id=%s
                      )
                    ORDER BY br.due_date ASC
                    """,
                    (student_id, student_id),
                )
                computed = list(cur.fetchall() or [])
                for loan in computed:
                    if loan.get('loan_id') in seen_loan_ids:
                        continue
                    end_date = loan.get('return_date') or datetime.utcnow()
                    amount = self._compute_fine(loan.get('due_date'), end_date)
                    if amount <= 0:
                        continue
                    loan.update({
                        'fine_id': None,
                        'amount': amount,
                        'fine_amount': amount,
                        'reason': 'Overdue book fine',
                        'status': 'unpaid',
                        'issued_date': None,
                        'paid_date': None,
                        'days_overdue': self._compute_days_overdue(loan.get('due_date'), end_date),
                        'is_paid': False,
                        'is_unpaid': True,
                        'source': 'computed',
                    })
                    self._convert_dates(loan, ['issue_date', 'due_date', 'return_date'])
                    fines.append(loan)

                return fines

    def get_fine_state_for_loan(self, loan_id: int):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT borrow_id, student_id, due_date, return_date
                    FROM borrow_records
                    WHERE borrow_id=%s
                    LIMIT 1
                    """,
                    (loan_id,),
                )
                loan = cur.fetchone()
                if not loan:
                    return None

                cur.execute(
                    """
                    SELECT
                        COUNT(*) AS fine_count,
                        COALESCE(SUM(CASE WHEN status IN ('unpaid', 'pending') THEN amount ELSE 0 END), 0) AS unpaid_amount,
                        SUM(CASE WHEN status='paid' THEN 1 ELSE 0 END) AS paid_count,
                        SUM(CASE WHEN status IN ('unpaid', 'pending') THEN 1 ELSE 0 END) AS unpaid_count,
                        SUM(CASE WHEN status='waived' THEN 1 ELSE 0 END) AS waived_count
                    FROM fines
                    WHERE borrow_id=%s
                    """,
                    (loan_id,),
                )
                summary = cur.fetchone() or {}
                fine_count = int(summary.get('fine_count') or 0)
                unpaid_amount = round(float(summary.get('unpaid_amount') or 0), 2)
                end_date = loan.get('return_date') or datetime.utcnow()
                computed_amount = self._compute_fine(loan.get('due_date'), end_date)
                days_overdue = self._compute_days_overdue(loan.get('due_date'), end_date)

                status = 'no_fine'
                payable_amount = 0.0
                if unpaid_amount > 0:
                    status = 'unpaid'
                    payable_amount = unpaid_amount
                elif fine_count == 0 and computed_amount > 0:
                    status = 'unpaid'
                    payable_amount = computed_amount
                elif int(summary.get('paid_count') or 0) > 0:
                    status = 'paid'
                elif int(summary.get('waived_count') or 0) > 0:
                    status = 'waived'

                return {
                    'loan_id': loan_id,
                    'student_id': loan.get('student_id'),
                    'status': status,
                    'fine_count': fine_count,
                    'paid_count': int(summary.get('paid_count') or 0),
                    'unpaid_count': int(summary.get('unpaid_count') or 0),
                    'waived_count': int(summary.get('waived_count') or 0),
                    'computed_amount': round(float(computed_amount or 0), 2),
                    'payable_amount': round(float(payable_amount or 0), 2),
                    'days_overdue': days_overdue,
                }

    def calculate_fine(self, loan_id: int):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT due_date, return_date FROM borrow_records WHERE borrow_id=%s LIMIT 1", (loan_id,))
                record = cur.fetchone()
                if not record:
                    return 0.0
                return self._get_outstanding_fine(
                    cur,
                    loan_id,
                    record.get('due_date'),
                    record.get('return_date') or datetime.utcnow(),
                )

    def pay_fine(self, loan_id: int):
        with get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT fine_id, borrow_id, student_id, amount, reason, status, issued_date, paid_date
                        FROM fines
                        WHERE borrow_id=%s
                          AND status IN ('unpaid', 'pending')
                        ORDER BY issued_date ASC, fine_id ASC
                        FOR UPDATE
                        """,
                        (loan_id,),
                    )
                    fines = list(cur.fetchall() or [])
                    if not fines:
                        cur.execute("SELECT COUNT(*) AS fine_count FROM fines WHERE borrow_id=%s", (loan_id,))
                        if int((cur.fetchone() or {}).get('fine_count') or 0) > 0:
                            conn.rollback()
                            return None

                        cur.execute(
                            """
                            SELECT borrow_id, student_id, due_date, return_date
                            FROM borrow_records
                            WHERE borrow_id=%s
                            LIMIT 1
                            FOR UPDATE
                            """,
                            (loan_id,),
                        )
                        loan = cur.fetchone()
                        if not loan:
                            conn.rollback()
                            return None

                        paid_at = datetime.utcnow()
                        fine_amount = self._compute_fine(loan.get('due_date'), loan.get('return_date') or paid_at)
                        if fine_amount <= 0:
                            conn.rollback()
                            return None

                        cur.execute(
                            """
                            INSERT INTO fines
                                (borrow_id, student_id, amount, reason, status, issued_date, paid_date)
                            VALUES (%s, %s, %s, %s, 'paid', %s, %s)
                            """,
                            (
                                loan_id,
                                loan['student_id'],
                                fine_amount,
                                'Overdue book fine',
                                paid_at,
                                paid_at,
                            ),
                        )
                        fine_id = cur.lastrowid
                        cur.execute(
                            """
                            SELECT fine_id, borrow_id, student_id, amount, reason, status, issued_date, paid_date
                            FROM fines
                            WHERE fine_id=%s
                            """,
                            (fine_id,),
                        )
                        paid_fines = [cur.fetchone()]
                        total_paid = fine_amount
                        conn.commit()

                        for fine in paid_fines:
                            fine['amount'] = round(float(fine.get('amount') or 0), 2)
                            self._convert_dates(fine, ['issued_date', 'paid_date'])
                        return {
                            'loan_id': loan_id,
                            'total_paid': total_paid,
                            'fines': paid_fines,
                        }

                    fine_ids = [fine['fine_id'] for fine in fines]
                    placeholders = ', '.join(['%s'] * len(fine_ids))
                    cur.execute(
                        f"""
                        UPDATE fines
                        SET status='paid',
                            paid_date=NOW()
                        WHERE fine_id IN ({placeholders})
                        """,
                        tuple(fine_ids),
                    )
                    cur.execute(
                        f"""
                        SELECT fine_id, borrow_id, student_id, amount, reason, status, issued_date, paid_date
                        FROM fines
                        WHERE fine_id IN ({placeholders})
                        ORDER BY issued_date ASC, fine_id ASC
                        """,
                        tuple(fine_ids),
                    )
                    paid_fines = list(cur.fetchall() or [])
                    total_paid = round(sum(float(fine.get('amount') or 0) for fine in paid_fines), 2)
                conn.commit()

                for fine in paid_fines:
                    fine['amount'] = round(float(fine.get('amount') or 0), 2)
                    self._convert_dates(fine, ['issued_date', 'paid_date'])
                return {
                    'loan_id': loan_id,
                    'total_paid': total_paid,
                    'fines': paid_fines,
                }
            except Exception:
                conn.rollback()
                raise

    def _compute_fine(self, due_date, returned_at):
        if not due_date or not returned_at:
            return 0.0
        if isinstance(returned_at, datetime):
            returned_at = returned_at.date()
        if isinstance(due_date, datetime):
            due_date = due_date.date()

        if returned_at > due_date:
            days_late = (returned_at - due_date).days
            return round(max(0.0, days_late * FINE_RATE_PER_DAY), 2)
        return 0.0

    def _get_outstanding_fine(self, cur, loan_id: int, due_date, returned_at):
        cur.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN status IN ('unpaid', 'pending') THEN amount ELSE 0 END), 0) AS unpaid_amount,
                COUNT(*) AS fine_count
            FROM fines
            WHERE borrow_id=%s
            """,
            (loan_id,),
        )
        fine_summary = cur.fetchone() or {}
        unpaid_amount = float(fine_summary.get('unpaid_amount') or 0)
        if unpaid_amount > 0:
            return round(unpaid_amount, 2)
        if int(fine_summary.get('fine_count') or 0) > 0:
            return 0.0
        return self._compute_fine(due_date, returned_at)

    def _compute_days_overdue(self, due_date, returned_at):
        if not due_date or not returned_at:
            return 0
        if isinstance(returned_at, datetime):
            returned_at = returned_at.date()
        if isinstance(due_date, datetime):
            due_date = due_date.date()

        if returned_at > due_date:
            return (returned_at - due_date).days
        return 0

    def find_loans_due_soon(self, days_before_due=3):
        """
        Find loans that are due within N days (and haven't been returned).
        Returns loans with student email and book info for reminder emails.
        """
        try:
            with get_connection() as conn:
                ensure_inventory_schema(conn)
                conn.commit()
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                            br.borrow_id,
                            br.student_id,
                            br.book_id,
                            br.copy_id,
                            bc.copy_code,
                            COALESCE(b.title, 'Unknown Book') AS book_title,
                            br.due_date,
                            s.email AS student_email,
                            COALESCE(NULLIF(s.full_name, ''), 'Student') AS student_name
                        FROM borrow_records br
                        LEFT JOIN books b ON br.book_id = b.book_id
                        LEFT JOIN book_copies bc ON br.copy_id = bc.copy_id AND bc.book_id = br.book_id
                        LEFT JOIN students s ON br.student_id = s.student_id
                        WHERE br.return_date IS NULL
                          AND br.due_date IS NOT NULL
                          AND br.status IN ('active', 'borrowed', 'overdue')
                          AND DATE(br.due_date) BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
                          AND s.email IS NOT NULL
                          AND TRIM(s.email) <> ''
                        ORDER BY br.due_date ASC
                        """,
                        (days_before_due,)
                    )
                    return cur.fetchall()
        except Exception as exc:
            logger.exception('Failed to query loans due soon')
            raise

    def find_overdue_loans(self):
        """
        Find active borrowed books whose due date has passed.
        Active loans are determined by return_date IS NULL; overdue is computed from due_date.
        """
        try:
            with get_connection() as conn:
                ensure_inventory_schema(conn)
                conn.commit()
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                            br.borrow_id,
                            br.student_id,
                            br.book_id,
                            br.copy_id,
                            bc.copy_code,
                            b.title AS book_title,
                            br.borrow_date,
                            br.due_date,
                            s.email AS student_email,
                            s.full_name AS student_name,
                            DATEDIFF(CURDATE(), DATE(br.due_date)) AS days_overdue,
                            ROUND(DATEDIFF(CURDATE(), DATE(br.due_date)) * %s, 2) AS fine_amount
                        FROM borrow_records br
                        LEFT JOIN books b ON br.book_id = b.book_id
                        LEFT JOIN book_copies bc ON br.copy_id = bc.copy_id AND bc.book_id = br.book_id
                        LEFT JOIN students s ON br.student_id = s.student_id
                        WHERE br.return_date IS NULL
                          AND br.due_date IS NOT NULL
                          AND DATE(br.due_date) < CURDATE()
                          AND br.status IN ('active', 'borrowed', 'overdue')
                        ORDER BY br.due_date ASC
                        """,
                        (FINE_RATE_PER_DAY,),
                    )
                    return cur.fetchall()
        except Exception:
            logger.exception('Failed to query overdue loans')
            raise

    def record_reminder(self, borrow_id, reminder_type, sent_to, status='sent', error_message=None):
        with get_connection() as conn:
            try:
                ensure_inventory_schema(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO loan_reminders
                            (borrow_id, reminder_type, sent_to, status, error_message)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (borrow_id, reminder_type, sent_to, status, error_message),
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
