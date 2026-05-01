from ....domain.services.fine_service import FineService


class PayFineUseCase:
    def __init__(self, fine_service: FineService):
        self.fine_service = fine_service

    def execute(self, loan_id: int):
        return self.fine_service.pay_fine(loan_id)
