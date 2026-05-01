from datetime import datetime

from ..database.db_connection import get_connection
from ...domain.repositories.loan_repository import LoanRepository


class LoanRepositoryImpl(LoanRepository):
    def create_loan(self, book_id: int, user_id: int, borrowed_at, due_date):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO borrow_records (book_id, user_id, borrowed_at, due_date, status) VALUES (%s, %s, %s, %s, 'borrowed')",
                    (book_id, user_id, borrowed_at, due_date)
                )
                conn.commit()
                return cur.lastrowid

    def close_loan(self, loan_id: int, returned_at):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE borrow_records SET returned_at=%s, status='returned' WHERE loan_id=%s",
                    (returned_at, loan_id)
                )
                conn.commit()
                cur.execute("SELECT * FROM borrow_records WHERE loan_id=%s", (loan_id,))
                return cur.fetchone()

    def find_active_loan(self, book_id: int, user_id: int):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM borrow_records WHERE book_id=%s AND user_id=%s AND status='borrowed' LIMIT 1",
                    (book_id, user_id)
                )
                return cur.fetchone()

    def calculate_fine(self, loan_id: int):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT due_date, returned_at FROM borrow_records WHERE loan_id=%s LIMIT 1", (loan_id,))
                record = cur.fetchone()
                if not record:
                    return 0.0
                due_date = record.get('due_date')
                returned_at = record.get('returned_at') or datetime.utcnow()
                if due_date and returned_at > due_date:
                    days_late = (returned_at - due_date).days
                    return max(0.0, days_late * 1.0)
                return 0.0
