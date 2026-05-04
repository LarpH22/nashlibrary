import logging
import re
from datetime import date, datetime
from ...domain.repositories.loan_repository import LoanRepository
from ...infrastructure.external.email_service import EmailService

logger = logging.getLogger(__name__)
EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


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
        loans = self.loan_repository.find_loans_due_soon(days_before_due)

        success_count = 0
        failed_count = 0
        skipped_count = 0
        failures = []

        for loan in loans:
            borrow_id = loan.get('borrow_id')
            student_email = (loan.get('student_email') or '').strip()
            try:
                validated_loan = self._validate_reminder_loan(loan)
                self._send_reminder_email(validated_loan, days_before_due)
                self._record_reminder_safe(borrow_id, 'due_soon', student_email, 'sent')
                success_count += 1
            except ValueError as exc:
                skipped_count += 1
                failures.append({'borrow_id': borrow_id, 'reason': str(exc), 'type': 'validation'})
                logger.warning('Skipping due reminder for borrow_id=%r: %s', borrow_id, exc)
                if student_email:
                    self._record_reminder_safe(borrow_id, 'due_soon', student_email, 'failed', str(exc))
            except Exception as exc:
                failed_count += 1
                failures.append({'borrow_id': borrow_id, 'reason': str(exc), 'type': 'send'})
                logger.warning('Failed to send due reminder for borrow_id=%r: %s', borrow_id, exc)
                if student_email:
                    self._record_reminder_safe(borrow_id, 'due_soon', student_email, 'failed', str(exc))

        result = {
            'sent': success_count,
            'failed': failed_count,
            'skipped': skipped_count,
            'total': len(loans),
            'failures': failures[:20],
        }
        logger.info("Loan reminders processed: %s", result)
        return result

    def send_overdue_reminders(self) -> dict:
        """Send reminders for loans that are already overdue."""
        try:
            loans = self.loan_repository.find_overdue_loans()
            success_count = 0
            failed_count = 0

            for loan in loans:
                student_email = loan.get('student_email')
                try:
                    validated_loan = self._validate_reminder_loan(loan)
                    self._send_overdue_email(validated_loan)
                    self._record_reminder_safe(loan.get('borrow_id'), 'overdue', student_email, 'sent')
                    success_count += 1
                except Exception as e:
                    logger.warning(f"Failed to send overdue reminder for loan {loan.get('borrow_id')}: {str(e)}")
                    if student_email:
                        self._record_reminder_safe(loan.get('borrow_id'), 'overdue', student_email, 'failed', str(e))
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
        
        # Format due date
        if hasattr(due_date, 'strftime'):
            due_date_str = due_date.strftime('%B %d, %Y')
        else:
            due_date_str = str(due_date)
        
        # Calculate days remaining
        if isinstance(due_date, datetime):
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

    def _send_overdue_email(self, loan: dict):
        student_email = loan.get('student_email')
        student_name = loan.get('student_name') or 'Student'
        book_title = loan.get('book_title', 'Unknown Book')
        due_date = loan.get('due_date')
        days_overdue = loan.get('days_overdue') or 0

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

    def _validate_reminder_loan(self, loan: dict):
        student_email = str(loan.get('student_email') or '').strip()
        if not student_email:
            raise ValueError(f"No email found for student {loan.get('student_id')}")
        if not EMAIL_PATTERN.match(student_email):
            raise ValueError(f"Invalid student email: {student_email}")

        due_date = loan.get('due_date')
        if not due_date:
            raise ValueError('Loan has no due date')
        if isinstance(due_date, datetime):
            normalized_due_date = due_date.date()
        elif isinstance(due_date, date):
            normalized_due_date = due_date
        elif isinstance(due_date, str):
            try:
                normalized_due_date = datetime.fromisoformat(due_date).date()
            except ValueError as exc:
                raise ValueError(f"Invalid due date: {due_date}") from exc
        else:
            raise ValueError(f"Unsupported due date value: {due_date!r}")

        validated = dict(loan)
        validated['student_email'] = student_email
        validated['student_name'] = loan.get('student_name') or 'Student'
        validated['book_title'] = loan.get('book_title') or 'Unknown Book'
        validated['due_date'] = normalized_due_date
        return validated

    def _record_reminder_safe(self, borrow_id, reminder_type, sent_to, status='sent', error_message=None):
        if not borrow_id or not sent_to:
            return
        try:
            self.loan_repository.record_reminder(borrow_id, reminder_type, sent_to, status, error_message)
        except Exception:
            logger.exception('Failed to record %s reminder status=%s for borrow_id=%r', reminder_type, status, borrow_id)
