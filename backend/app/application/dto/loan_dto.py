from dataclasses import dataclass
from datetime import datetime


@dataclass
class LoanDTO:
    loan_id: int
    book_id: int
    user_id: int
    borrowed_at: datetime
    due_date: datetime
    returned_at: datetime | None
    status: str
