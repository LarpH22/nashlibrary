import secrets
from datetime import datetime, timedelta

from ....domain.services.auth_service import AuthService
from ....infrastructure.external.email_service import EmailService


class ForgotPasswordUseCase:
    """Use case for handling forgot password requests"""

    def __init__(self, auth_service: AuthService, email_service: EmailService):
        self.auth_service = auth_service
        self.email_service = email_service

    def execute(self, email: str) -> dict:
        """
        Execute forgot password process

        Args:
            email: User email

        Returns:
            dict: Result message
        """
        # Find active student by email
        student = self.auth_service.student_repo.find_student_by_email(email)
        if not student or student.get('status') != 'active':
            raise ValueError("No active account found with this email")

        # Generate reset token and expiration
        reset_token = secrets.token_urlsafe(32)
        reset_expires = datetime.utcnow() + timedelta(hours=1)

        # Update student with reset token
        self.auth_service.student_repo.update_student_reset_token(
            student['student_id'], reset_token, reset_expires
        )

        # Send reset email
        reset_url = f"http://localhost:3000/reset-password?token={reset_token}"
        email_body = f"""Hello {student['full_name']},

You requested a password reset for your library account.

Click the link below to reset your password (valid for 1 hour):
{reset_url}

If you did not request this, please ignore this email.

Best regards,
Library Management System
"""
        html_body = f"""
        <html>
            <body style="font-family:Arial,Helvetica,sans-serif;background:#f4f7fb;color:#1f2937;padding:20px;">
                <div style="max-width:600px;margin:0 auto;padding:30px;background:#ffffff;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
                    <h1 style="font-size:24px;margin-bottom:16px;color:#0f172a;">Reset your NashLibrary password</h1>
                    <p style="font-size:16px;line-height:1.6;margin-bottom:24px;">Hello {student['full_name']},</p>
                    <p style="font-size:16px;line-height:1.6;margin-bottom:24px;">You requested a password reset for your library account. Click the button below to reset your password.</p>
                    <a href="{reset_url}" style="display:inline-block;padding:14px 24px;background:#0f766e;color:#ffffff;text-decoration:none;border-radius:8px;font-weight:600;">Reset Password</a>
                    <p style="font-size:14px;line-height:1.6;color:#475569;margin-top:24px;">This link will expire in 1 hour.</p>
                    <p style="font-size:14px;word-break:break-all;color:#2563eb;margin-top:12px;">{reset_url}</p>
                    <p style="font-size:14px;line-height:1.6;color:#475569;margin-top:24px;">If you did not request this, please ignore this email.</p>
                    <p style="font-size:14px;line-height:1.6;color:#475569;margin-top:24px;">Best regards,<br/>NashLibrary Team</p>
                </div>
            </body>
        </html>
        """

        self.email_service.send_email(
            subject="Password Reset Request - NashLibrary",
            recipients=[email],
            body=email_body,
            html_body=html_body
        )

        return {'message': 'Password reset link sent to your email'}