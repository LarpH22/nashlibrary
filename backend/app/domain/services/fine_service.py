from datetime import datetime

from ..repositories.loan_repository import LoanRepository


class FineService:
    def __init__(self, loan_repository: LoanRepository):
        self.loan_repository = loan_repository

    def calculate_fine(self, loan_id: int):
        return self.loan_repository.calculate_fine(loan_id)

    def pay_fine(self, loan_id: int):
        return self.loan_repository.close_loan(loan_id, datetime.utcnow())
