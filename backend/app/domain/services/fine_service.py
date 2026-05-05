from ..repositories.loan_repository import LoanRepository


class FineService:
    def __init__(self, loan_repository: LoanRepository):
        self.loan_repository = loan_repository

    def calculate_fine(self, loan_id: int):
        return self.loan_repository.calculate_fine(loan_id)

    def pay_fine(self, loan_id: int):
        return self.loan_repository.pay_fine(loan_id)

    def get_fine_state_for_loan(self, loan_id: int):
        return self.loan_repository.get_fine_state_for_loan(loan_id)

    def list_student_fines(self, student_id: int):
        return self.loan_repository.find_fines_by_student_id(student_id)
