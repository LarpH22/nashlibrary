import logging
from datetime import datetime
from ...domain.repositories.loan_repository import LoanRepository
from ...infrastructure.external.email_service import EmailService

logger = logging.getLogger(__name__)


class LoanReminderService:
    """Service to send email reminders for upcoming due dates"""
    
    def __init__(self, loan_repository: LoanRepository, email_service: EmailService):
        self.loan_repository = loan_repository
        self.email_service = email_service

    def send_due_date_reminders(self, days_before_due: int = 3) -> dict:
        """
        Send email reminders for loans due within N days.
        Returns a dict with success/failure counts.
        """
        try:
            loans = self.loan_repository.find_loans_due_soon(days_before_due)
            
            success_count = 0
            failed_count = 0
            
            for loan in loans:
                try:
                    self._send_reminder_email(loan, days_before_due)
                    success_count += 1
                except Exception as e:
                    logger.warning(f"Failed to send reminder for loan {loan.get('borrow_id')}: {str(e)}")
                    failed_count += 1
            
            result = {
                'sent': success_count,
                'failed': failed_count,
                'total': success_count + failed_count
            }
            logger.info(f"Loan reminders sent: {result}")
            return result
            
        except Exception as exc:
            logger.exception('Failed to send loan reminders')
            raise

    def send_overdue_reminders(self) -> dict:
        """Send reminders for loans that are already overdue."""
        try:
            loans = self.loan_repository.find_overdue_loans()
            success_count = 0
            failed_count = 0

            for loan in loans:
                student_email = loan.get('student_email')
                try:
                    self._send_overdue_email(loan)
                    self.loan_repository.record_reminder(loan.get('borrow_id'), 'overdue', student_email, 'sent')
                    success_count += 1
                except Exception as e:
                    logger.warning(f"Failed to send overdue reminder for loan {loan.get('borrow_id')}: {str(e)}")
                    if student_email:
                        self.loan_repository.record_reminder(loan.get('borrow_id'), 'overdue', student_email, 'failed', str(e))
                    failed_count += 1

            result = {'sent': success_count, 'failed': failed_count, 'total': success_count + failed_count}
            logger.info(f"Overdue loan reminders sent: {result}")
            return result
        except Exception:
            logger.exception('Failed to send overdue loan reminders')
            raise

    def _send_reminder_email(self, loan: dict, days_before_due: int):
        """Send a single reminder email"""
        student_email = loan.get('student_email')
        student_name = loan.get('student_name')
        book_title = loan.get('book_title', 'Unknown Book')
        due_date = loan.get('due_date')
        
        if not student_email:
            raise ValueError(f"No email found for student {loan.get('student_id')}")
        
        # Format due date
        if hasattr(due_date, 'strftime'):
            due_date_str = due_date.strftime('%B %d, %Y')
        else:
            due_date_str = str(due_date)
        
        # Calculate days remaining
        if hasattr(due_date, 'date'):
            due_date_obj = due_date.date()
        else:
            due_date_obj = due_date
        
        today = datetime.utcnow().date()
        days_remaining = (due_date_obj - today).days
        
        subject = f"Library Book Due Soon: {book_title}"
        
        body_text = f"""Hi {student_name},

This is a reminder that your borrowed book "{book_title}" is due on {due_date_str}.

You have {days_remaining} days remaining to return this book. Please visit the library or log in to your account to manage your loans.

Best regards,
Library System
"""
        
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333;">Library Book Due Soon</h2>
        <p>Hi {student_name},</p>
        <p>This is a reminder that your borrowed book is due soon:</p>
        <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #2c3e50; margin: 20px 0;">
            <p style="margin: 5px 0;"><strong>Book:</strong> {book_title}</p>
            <p style="margin: 5px 0;"><strong>Due Date:</strong> {due_date_str}</p>
            <p style="margin: 5px 0;"><strong>Days Remaining:</strong> <span style="color: #e74c3c; font-weight: bold;">{days_remaining}</span></p>
        </div>
        <p>Please return this book on time to avoid late fees. You can manage your loans by logging into your account.</p>
        <p>Best regards,<br/>Library System</p>
    </div>
</body>
</html>
        """
        
        self.email_service.send_email(
            subject=subject,
            recipients=[student_email],
            body=body_text,
            html_body=html_body
        )
        self.loan_repository.record_reminder(loan.get('borrow_id'), 'due_soon', student_email, 'sent')

    def _send_overdue_email(self, loan: dict):
        student_email = loan.get('student_email')
        student_name = loan.get('student_name') or 'Student'
        book_title = loan.get('book_title', 'Unknown Book')
        due_date = loan.get('due_date')
        days_overdue = loan.get('days_overdue') or 0

        if not student_email:
            raise ValueError(f"No email found for student {loan.get('student_id')}")

        due_date_str = due_date.strftime('%B %d, %Y') if hasattr(due_date, 'strftime') else str(due_date)
        subject = f"Overdue Library Book: {book_title}"
        body_text = f"""Hi {student_name},

Your borrowed book "{book_title}" was due on {due_date_str} and is now {days_overdue} days overdue.

Please return it as soon as possible or contact the library if you need help with your account.

Best regards,
Library System
"""
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #b42318;">Overdue Library Book</h2>
        <p>Hi {student_name},</p>
        <p>Your borrowed book is overdue:</p>
        <div style="background-color: #fff4f2; padding: 15px; border-left: 4px solid #b42318; margin: 20px 0;">
            <p style="margin: 5px 0;"><strong>Book:</strong> {book_title}</p>
            <p style="margin: 5px 0;"><strong>Due Date:</strong> {due_date_str}</p>
            <p style="margin: 5px 0;"><strong>Days Overdue:</strong> {days_overdue}</p>
        </div>
        <p>Please return it as soon as possible to reduce additional penalties.</p>
        <p>Best regards,<br/>Library System</p>
    </div>
</body>
</html>
        """
        self.email_service.send_email(subject=subject, recipients=[student_email], body=body_text, html_body=html_body)
