from dataclasses import dataclass
from datetime import datetime


@dataclass
class Loan:
    book_id: int
    user_id: int
    borrowed_at: datetime
    due_date: datetime
    returned_at: datetime | None = None
    status: str = 'borrowed'
    loan_id: int | None = None
