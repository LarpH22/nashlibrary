from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserModel:
    user_id: int
    email: str
    full_name: str
    role: str
    status: str
    password_hash: str
    created_at: datetime


@dataclass
class BookModel:
    book_id: int
    title: str
    author: str
    isbn: str
    status: str
    available_copies: int
    total_copies: int


@dataclass
class FineModel:
    fine_id: int
    loan_id: int
    amount: float
    paid: bool
    created_at: datetime


@dataclass
class LoanModel:
    loan_id: int
    book_id: int
    user_id: int
    borrowed_at: datetime
    due_date: datetime
    returned_at: datetime | None
    status: str
