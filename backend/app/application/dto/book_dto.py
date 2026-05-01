from dataclasses import dataclass


@dataclass
class BookDTO:
    book_id: int
    title: str
    author: str
    isbn: str
    status: str
    available_copies: int
    total_copies: int
