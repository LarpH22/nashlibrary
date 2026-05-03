from ....domain.services.loan_service import LoanService


class GetStudentLoansUseCase:
    def __init__(self, loan_service: LoanService):
        self.loan_service = loan_service

    def execute(self, student_id: int):
        return self.loan_service.get_loans_by_student(student_id)
