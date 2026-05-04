import logging
from flask import jsonify, request
from flask_jwt_extended import get_jwt

from ...domain.services.loan_reminder_service import LoanReminderService
from ...infrastructure.repositories_impl.loan_repository_impl import LoanRepositoryImpl
from ...infrastructure.external.email_service import EmailService

logger = logging.getLogger(__name__)


class LoanReminderController:
    """Controller to manage loan reminders"""
    
    def __init__(self, email_service: EmailService):
        self.loan_repository = LoanRepositoryImpl()
        self.email_service = email_service
        self.reminder_service = LoanReminderService(self.loan_repository, email_service)

    def _require_admin_or_librarian(self):
        """Check if user is admin or librarian"""
        jwt_claims = get_jwt()
        if jwt_claims.get('role') not in ['admin', 'librarian']:
            return jsonify({'message': 'Admin or librarian access required'}), 403
        return None

    def send_due_reminders(self):
        """
        POST /reminders/send-due-reminders
        Sends email reminders for loans due within N days (default 3)
        Query param: days (optional, default 3)
        """
        auth_error = self._require_admin_or_librarian()
        if auth_error:
            return auth_error

        try:
            days = request.args.get('days', 3, type=int)
            
            if days < 1 or days > 30:
                return jsonify({'message': 'Days must be between 1 and 30'}), 400
            
            result = self.reminder_service.send_due_date_reminders(days_before_due=days)
            
            return jsonify({
                'message': 'Reminders sent successfully',
                'data': {
                    'sent': result['sent'],
                    'failed': result['failed'],
                    'total': result['total']
                }
            }), 200
            
        except Exception as e:
            logger.exception('Error sending reminders')
            return jsonify({'message': f'Error sending reminders: {str(e)}'}), 500

    def get_loans_due_soon(self):
        """
        GET /reminders/loans-due-soon
        Get list of loans due within N days (default 3)
        Query param: days (optional, default 3)
        """
        auth_error = self._require_admin_or_librarian()
        if auth_error:
            return auth_error

        try:
            days = request.args.get('days', 3, type=int)
            
            if days < 1 or days > 30:
                return jsonify({'message': 'Days must be between 1 and 30'}), 400
            
            loans = self.loan_repository.find_loans_due_soon(days_before_due=days)
            
            # Format dates for JSON
            for loan in loans:
                if loan.get('due_date') and hasattr(loan['due_date'], 'isoformat'):
                    loan['due_date'] = loan['due_date'].isoformat()
            
            return jsonify({
                'data': loans,
                'count': len(loans)
            }), 200
            
        except Exception as e:
            logger.exception('Error fetching loans due soon')
            return jsonify({'message': f'Error fetching loans: {str(e)}'}), 500
