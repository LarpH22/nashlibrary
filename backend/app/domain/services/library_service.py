from ..repositories.book_repository import BookRepository
from ..repositories.loan_repository import LoanRepository


class LibraryService:
    def __init__(self, book_repository: BookRepository, loan_repository: LoanRepository):
        self.book_repository = book_repository
        self.loan_repository = loan_repository

    def add_book(self, title: str, author: str, isbn: str, available_copies: int = 1, total_copies: int = 1):
        return self.book_repository.add_book(title, author, isbn, available_copies, total_copies)

    def borrow_book(self, book_id: int, user_id: int, borrowed_at, due_date):
        active_loan = self.loan_repository.find_active_loan(book_id, user_id)
        if active_loan:
            raise ValueError('User already has an active loan for this book')
        book = self.book_repository.find_by_id(book_id)
        if not book or book.get('available_copies', 0) <= 0:
            raise ValueError('Book is not available')
        return self.loan_repository.create_loan(book_id, user_id, borrowed_at, due_date)

    def return_book(self, loan_id: int, returned_at, student_id: int | None = None):
        return self.loan_repository.close_loan(loan_id, returned_at, student_id)
