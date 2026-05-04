from flask import Blueprint
from flask_jwt_extended import jwt_required
from ...infrastructure.external.email_service import EmailService
from ...presentation.controllers.loan_reminder_controller import LoanReminderController

reminder_bp = Blueprint('reminders', __name__)

# Initialize the controller with email service
email_service = EmailService()
controller = LoanReminderController(email_service)


@reminder_bp.post('/send-due-reminders')
@jwt_required()
def send_due_reminders():
    """Send email reminders for loans due soon"""
    return controller.send_due_reminders()


@reminder_bp.get('/loans-due-soon')
@jwt_required()
def get_loans_due_soon():
    """Get loans due within N days"""
    return controller.get_loans_due_soon()


@reminder_bp.post('/send-overdue-reminders')
@jwt_required()
def send_overdue_reminders():
    """Send email reminders for overdue loans"""
    return controller.send_overdue_reminders()


@reminder_bp.get('/overdue-loans')
@jwt_required()
def get_overdue_loans():
    """Get overdue loans"""
    return controller.get_overdue_loans()
