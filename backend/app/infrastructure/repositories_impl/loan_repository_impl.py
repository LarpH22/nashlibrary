import logging
from datetime import datetime, date

from ..database.db_connection import get_connection
from ...domain.repositories.loan_repository import LoanRepository

FINE_RATE_PER_DAY = 1.0

logger = logging.getLogger(__name__)


class LoanRepositoryImpl(LoanRepository):
    def create_loan(self, book_id: int, user_id: int, borrowed_at, due_date):
        # Map the domain user_id to the borrow_records.student_id column.
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO borrow_records (student_id, book_id, borrow_date, due_date, status) VALUES (%s, %s, %s, %s, 'active')",
                    (user_id, book_id, borrowed_at, due_date)
                )
                conn.commit()
                return cur.lastrowid

    def close_loan(self, loan_id: int, returned_at):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE borrow_records SET return_date=%s, status='returned' WHERE borrow_id=%s",
                    (returned_at, loan_id)
                )
                conn.commit()
                cur.execute("SELECT * FROM borrow_records WHERE borrow_id=%s", (loan_id,))
                loan = cur.fetchone()

                if loan:
                    due_date = loan.get('due_date')
                    student_id = loan.get('student_id')
                    fine_amount = self._compute_fine(due_date, returned_at)
                    loan['fine_amount'] = fine_amount
                    loan['days_overdue'] = self._compute_days_overdue(due_date, returned_at)

                    if fine_amount > 0 and student_id:
                        cur.execute(
                            "SELECT 1 FROM fines WHERE borrow_id=%s LIMIT 1",
                            (loan_id,)
                        )
                        existing_fine = cur.fetchone()
                        if not existing_fine:
                            cur.execute(
                                "INSERT INTO fines (borrow_id, student_id, amount, reason, status, issued_date) VALUES (%s, %s, %s, %s, 'pending', %s)",
                                (loan_id, student_id, fine_amount, 'Overdue book return', returned_at.date())
                            )
                            conn.commit()
                return loan

    def find_active_loan(self, book_id: int, user_id: int):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM borrow_records WHERE book_id=%s AND student_id=%s AND status='active' LIMIT 1",
                    (book_id, user_id)
                )
                return cur.fetchone()

    def find_loans_by_student_id(self, student_id: int):
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                            br.borrow_id AS loan_id,
                            br.student_id,
                            br.book_id,
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
                        LEFT JOIN book_authors ba ON b.book_id = ba.book_id
                        LEFT JOIN authors a ON ba.author_id = a.author_id
                        WHERE br.student_id = %s
                        GROUP BY br.borrow_id, br.student_id, br.book_id, b.title, b.isbn, b.publisher, b.publication_year, br.borrow_date, br.due_date, br.return_date, br.status
                        ORDER BY br.borrow_date DESC
                        """,
                        (student_id,)
                    )
                    loans = cur.fetchall()

                    # Convert all date/datetime objects to ISO format strings for JSON serialization
                    if loans:
                        for loan in loans:
                            due_date = loan.get('due_date')
                            return_date = loan.get('return_date')
                            loan['fine_amount'] = self._compute_fine(due_date, return_date or datetime.utcnow())
                            loan['days_overdue'] = self._compute_days_overdue(due_date, return_date or datetime.utcnow())

                            for field_name in ['issue_date', 'due_date', 'return_date']:
                                if field_name in loan and loan[field_name] is not None:
                                    value = loan[field_name]
                                    if hasattr(value, 'isoformat'):
                                        loan[field_name] = value.isoformat()
                                    elif isinstance(value, str):
                                        pass

                    return loans
        except Exception as exc:
            logger.exception('Failed to query loans for student_id=%r', student_id)
            raise
    def calculate_fine(self, loan_id: int):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT due_date, return_date FROM borrow_records WHERE borrow_id=%s LIMIT 1", (loan_id,))
                record = cur.fetchone()
                if not record:
                    return 0.0
                due_date = record.get('due_date')
                returned_at = record.get('return_date') or datetime.utcnow()
                return self._compute_fine(due_date, returned_at)

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
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                            br.borrow_id,
                            br.student_id,
                            br.book_id,
                            b.title AS book_title,
                            br.due_date,
                            s.email AS student_email,
                            s.full_name AS student_name
                        FROM borrow_records br
                        LEFT JOIN books b ON br.book_id = b.book_id
                        LEFT JOIN student_accounts s ON br.student_id = s.student_id
                        WHERE br.status = 'active'
                        AND DATE(br.due_date) BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
                        AND s.email IS NOT NULL
                        ORDER BY br.due_date ASC
                        """,
                        (days_before_due,)
                    )
                    return cur.fetchall()
        except Exception as exc:
            logger.exception('Failed to query loans due soon')
            raise
