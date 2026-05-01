from dataclasses import dataclass


@dataclass
class Book:
    title: str
    author: str
    isbn: str
    status: str = 'available'
    available_copies: int = 1
    total_copies: int = 1
    book_id: int | None = None
