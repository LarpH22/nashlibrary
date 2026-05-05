from flask import jsonify, request

from ...application.use_cases.fine.calculate_fine import CalculateFineUseCase
from ...application.use_cases.fine.pay_fine import PayFineUseCase
from ...domain.services.fine_service import FineService
from ...infrastructure.repositories_impl.loan_repository_impl import LoanRepositoryImpl


class FineController:
    def __init__(self):
        self.loan_repository = LoanRepositoryImpl()
        self.fine_service = FineService(self.loan_repository)
        self.calculate_fine_use_case = CalculateFineUseCase(self.fine_service)
        self.pay_fine_use_case = PayFineUseCase(self.fine_service)

    def _parse_loan_id(self, loan_id):
        if not loan_id:
            return None, (jsonify({'message': 'loan_id is required'}), 400)
        try:
            loan_id = int(loan_id)
        except (TypeError, ValueError):
            return None, (jsonify({'message': 'loan_id must be a valid integer'}), 400)
        if loan_id <= 0:
            return None, (jsonify({'message': 'loan_id must be greater than zero'}), 400)
        return loan_id, None

    def calculate_fine(self):
        loan_id, error_response = self._parse_loan_id(request.args.get('loan_id'))
        if error_response:
            return error_response

        fine_state = self.fine_service.get_fine_state_for_loan(loan_id)
        if not fine_state:
            return jsonify({'message': 'Loan not found'}), 404

        fine = self.calculate_fine_use_case.execute(loan_id)
        message = 'Fine calculated'
        if fine_state.get('status') == 'paid':
            message = 'Fine already paid'
        elif fine <= 0:
            message = 'No fine exists for this loan'

        return jsonify({
            'message': message,
            'loan_id': loan_id,
            'fine_amount': fine,
            'status': fine_state.get('status'),
            'days_overdue': fine_state.get('days_overdue', 0),
        }), 200

    def pay_fine(self):
        data = request.get_json() or {}
        loan_id, error_response = self._parse_loan_id(data.get('loan_id'))
        if error_response:
            return error_response

        fine_state = self.fine_service.get_fine_state_for_loan(loan_id)
        if not fine_state:
            return jsonify({'message': 'Loan not found'}), 404
        if fine_state.get('status') == 'paid':
            return jsonify({'message': 'Fine already paid'}), 409
        if fine_state.get('status') != 'unpaid' or fine_state.get('payable_amount', 0) <= 0:
            return jsonify({'message': 'No fine exists for this loan'}), 404

        payment = self.pay_fine_use_case.execute(loan_id)
        if not payment:
            return jsonify({'message': 'No fine exists for this loan'}), 404
        return jsonify({'message': 'Fine paid', 'fine': payment}), 200

    def list_student_fines(self, current_user):
        if not current_user or current_user.get('role') != 'student':
            return jsonify({'message': 'Student access is required'}), 403

        student_id = current_user.get('student_id')
        try:
            student_id = int(student_id)
        except (TypeError, ValueError):
            return jsonify({'message': 'Student profile not found'}), 404

        fines = self.fine_service.list_student_fines(student_id)
        unpaid = [fine for fine in fines if fine.get('status') in ('unpaid', 'pending')]
        paid = [fine for fine in fines if fine.get('status') == 'paid']
        waived = [fine for fine in fines if fine.get('status') == 'waived']
        return jsonify({
            'message': 'Student fines loaded',
            'fines': fines,
            'summary': {
                'total_count': len(fines),
                'unpaid_count': len(unpaid),
                'paid_count': len(paid),
                'waived_count': len(waived),
                'total_unpaid': round(sum(float(fine.get('amount') or 0) for fine in unpaid), 2),
                'total_paid': round(sum(float(fine.get('amount') or 0) for fine in paid), 2),
            }
        }), 200
