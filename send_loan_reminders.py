"""
Command-line utility to manage loan reminders.
Run with: python -m scripts.send_loan_reminders [--days 3]
"""
import sys
import argparse
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from backend.app import create_app
from backend.app.domain.services.loan_reminder_service import LoanReminderService
from backend.app.infrastructure.repositories_impl.loan_repository_impl import LoanRepositoryImpl
from backend.app.infrastructure.external.email_service import EmailService


def send_reminders(days_before_due=3, include_overdue=True):
    """Send email reminders for loans due within N days"""
    app = create_app()
    
    with app.app_context():
        # Initialize services
        email_service = EmailService(app)
        loan_repository = LoanRepositoryImpl()
        reminder_service = LoanReminderService(loan_repository, email_service)
        
        # Send reminders
        result = reminder_service.send_due_date_reminders(days_before_due)
        overdue_result = reminder_service.send_overdue_reminders() if include_overdue else {'sent': 0, 'failed': 0, 'total': 0}
        
        print(f"\n✓ Loan Reminders Sent")
        print(f"  - Success: {result['sent']}")
        print(f"  - Failed: {result['failed']}")
        print(f"  - Total: {result['total']}")
        print(f"  - Overdue Success: {overdue_result['sent']}")
        print(f"  - Overdue Failed: {overdue_result['failed']}")
        
        return {'due_soon': result, 'overdue': overdue_result}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send loan due date reminders')
    parser.add_argument('--days', type=int, default=3, 
                       help='Send reminders for loans due within N days (default: 3)')
    parser.add_argument('--skip-overdue', action='store_true', help='Only send upcoming due-date reminders')
    args = parser.parse_args()
    
    try:
        send_reminders(days_before_due=args.days, include_overdue=not args.skip_overdue)
    except Exception as e:
        print(f"✗ Error sending reminders: {str(e)}", file=sys.stderr)
        sys.exit(1)
