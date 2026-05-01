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

    def calculate_fine(self):
        loan_id = request.args.get('loan_id')
        if not loan_id:
            return jsonify({'message': 'loan_id is required'}), 400
        fine = self.calculate_fine_use_case.execute(int(loan_id))
        return jsonify({'loan_id': loan_id, 'fine_amount': fine}), 200

    def pay_fine(self):
        data = request.get_json() or {}
        loan_id = data.get('loan_id')
        if not loan_id:
            return jsonify({'message': 'loan_id is required'}), 400
        payment = self.pay_fine_use_case.execute(int(loan_id))
        return jsonify({'message': 'Fine paid', 'loan': payment}), 200
