from abc import ABC, abstractmethod


class LoanRepository(ABC):
    @abstractmethod
    def create_loan(self, book_id: int, user_id: int, borrowed_at, due_date):
        raise NotImplementedError

    @abstractmethod
    def close_loan(self, loan_id: int, returned_at, student_id: int | None = None):
        raise NotImplementedError

    @abstractmethod
    def find_active_loan(self, book_id: int, user_id: int):
        raise NotImplementedError

    @abstractmethod
    def find_loans_by_student_id(self, student_id: int):
        raise NotImplementedError

    @abstractmethod
    def calculate_fine(self, loan_id: int):
        raise NotImplementedError

    @abstractmethod
    def find_loans_due_soon(self, days_before_due=3):
        raise NotImplementedError
