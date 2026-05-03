from ...domain.repositories.loan_repository import LoanRepository


class LoanService:
    def __init__(self, loan_repository: LoanRepository):
        self.loan_repository = loan_repository

    def get_loans_by_student(self, student_id: int):
        if not student_id:
            return []
        return self.loan_repository.find_loans_by_student_id(student_id) or []
