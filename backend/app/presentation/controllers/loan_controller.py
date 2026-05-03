from flask import jsonify, request, has_request_context

from ...application.use_cases.loan.get_student_loans import GetStudentLoansUseCase
from ...domain.services.loan_service import LoanService
from ...infrastructure.repositories_impl.loan_repository_impl import LoanRepositoryImpl


class LoanController:
    def __init__(self):
        self.loan_repository = LoanRepositoryImpl()
        self.loan_service = LoanService(self.loan_repository)
        self.get_student_loans_use_case = GetStudentLoansUseCase(self.loan_service)

    def list_student_loans(self, current_user):
        if not current_user:
            return jsonify({'message': 'Authentication required'}), 401

        if current_user.get('role') != 'student':
            return jsonify({'message': 'Student access required'}), 403

        student_id_value = current_user.get('student_id')
        if student_id_value in (None, '', 'undefined', 'null'):
            return jsonify({'message': 'Student ID not available for authenticated user'}), 400

        try:
            student_id = int(student_id_value)
            if student_id <= 0:
                raise ValueError('Student ID must be a positive integer')
        except (TypeError, ValueError) as exc:
            return jsonify({'message': 'Invalid student ID in token', 'error': str(exc)}), 400

        loans = self.get_student_loans_use_case.execute(student_id)
        return jsonify(loans), 200
