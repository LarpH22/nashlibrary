import uuid
import os
from datetime import datetime, timedelta
from typing import Optional

from ....domain.services.auth_service import AuthService
from ....domain.services.validation_service import ValidationService
from ....infrastructure.external.email_service import EmailService
from ....infrastructure.external.file_storage import FileStorage
from ....infrastructure.config import Config


class SecureStudentRegistrationUseCase:
    """Use case for secure student registration with email verification"""

    def __init__(self, auth_service: AuthService, email_service: EmailService,
                 file_storage: FileStorage, validation_service: ValidationService):
        self.auth_service = auth_service
        self.email_service = email_service
        self.file_storage = file_storage
        self.validation_service = validation_service

    def execute(self, email: str, full_name: str, password: str,
                student_id: str, registration_document,
                department: str, year_level) -> dict:
        """
        Execute secure student registration process

        Args:
            email: Student email
            full_name: Student full name
            password: Student password
            student_id: Student ID (format: 241-0449)
            registration_document: Uploaded file object
            department: Student department or program
            year_level: Student year level

        Returns:
            dict: Registration result with message and request_id
        """
        # Sanitize inputs
        email = self.validation_service.sanitize_text(email)
        full_name = self.validation_service.sanitize_text(full_name)
        student_id = self.validation_service.sanitize_text(student_id)
        department = self.validation_service.sanitize_text(department)
        year_level = self.validation_service.sanitize_text(str(year_level))

        # Validate required fields
        valid, message = self.validation_service.validate_required_fields(
            email=email, full_name=full_name, password=password, student_id=student_id,
            department=department, year_level=year_level
        )
        if not valid:
            raise ValueError(message)

        # Validate email format and domain restrictions
        valid, message = self.validation_service.validate_email(email)
        if not valid:
            raise ValueError(message)

        # Validate student ID format
        if not self.validation_service.validate_student_id(student_id):
            raise ValueError("Invalid student ID format. Must be in format 241-0449 (3 digits, dash, 4 digits)")

        # Validate year level
        try:
            year_level_value = int(year_level)
        except (TypeError, ValueError):
            raise ValueError("Year level must be a valid number")
        if year_level_value < 1 or year_level_value > 10:
            raise ValueError("Year level must be between 1 and 10")

        if not department:
            raise ValueError("Department / Program is required")

        # Validate password strength
        valid, message = self.validation_service.validate_password_strength(password)
        if not valid:
            raise ValueError(message)

        # Validate file
        if not registration_document:
            raise ValueError("Registration document is required")
        valid, message = self.validation_service.validate_file(registration_document)
        if not valid:
            raise ValueError(message)

        # Check uniqueness (email and student_id)
        if self.auth_service.student_repo.find_student_by_email(email):
            raise ValueError("Email already registered")
        if self.auth_service.student_repo.find_student_by_student_number(student_id):
            raise ValueError("Student ID already registered")

        # Check registration requests table too
        if self.auth_service.student_repo.find_registration_request_by_email(email):
            raise ValueError("Email already has a pending registration request")
        if self.auth_service.student_repo.find_registration_request_by_student_number(student_id):
            raise ValueError("Student ID already has a pending registration request")

        # Save the uploaded file
        filename = self.file_storage.save(registration_document, f"{student_id}_{email}_registration.pdf")

        # Hash password
        password_hash = self.auth_service.hash_password(password)

        # Generate verification token
        verification_token = str(uuid.uuid4())

        # Create registration request
        request_id = self.auth_service.student_repo.create_registration_request(
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            student_number=student_id,
            registration_document=filename,
            department=department,
            year_level=year_level_value,
            verification_token=verification_token
        )

        # Send verification email
        self._send_verification_email(email, full_name, verification_token)

        return {
            'message': 'Registration request submitted successfully. Please check your email to verify your account.',
            'request_id': request_id
        }

    def _send_verification_email(self, email: str, full_name: str, token: str):
        """Send email verification link"""
        verification_url = f"{Config.FRONTEND_URL}/verify-email?token={token}"

        subject = "Verify Your LIBRASYS Account"
        body = f"""
Dear {full_name},

Welcome to LIBRASYS! Thank you for registering with our library system.

To complete your registration and activate your account, please verify your email address by clicking the link below:

{verification_url}

This verification link will expire in 24 hours for security reasons.

If you did not request this registration, please ignore this email.

Best regards,
LIBRASYS Team
LIBRASYS
        """

        html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your LIBRASYS Account</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: #f8fafc;
            color: #334155;
            line-height: 1.6;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px 30px;
            text-align: center;
            color: white;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.025em;
        }}
        .header p {{
            margin: 8px 0 0 0;
            font-size: 16px;
            opacity: 0.9;
        }}
        .content {{
            padding: 40px 30px;
        }}
        .greeting {{
            font-size: 20px;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 16px;
        }}
        .message {{
            font-size: 16px;
            color: #64748b;
            margin-bottom: 32px;
            line-height: 1.7;
        }}
        .button-container {{
            text-align: center;
            margin: 40px 0;
        }}
        .verify-button {{
            display: inline-block;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            text-decoration: none;
            padding: 16px 32px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 16px;
            text-align: center;
            box-shadow: 0 4px 14px 0 rgba(16, 185, 129, 0.39);
            transition: all 0.2s ease;
            border: none;
            cursor: pointer;
        }}
        .verify-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px 0 rgba(16, 185, 129, 0.5);
        }}
        .warning {{
            background-color: #fef3c7;
            border: 1px solid #f59e0b;
            border-radius: 8px;
            padding: 16px;
            margin: 24px 0;
            font-size: 14px;
            color: #92400e;
        }}
        .warning strong {{
            color: #78350f;
        }}
        .footer {{
            background-color: #f8fafc;
            padding: 30px;
            text-align: center;
            border-top: 1px solid #e2e8f0;
        }}
        .footer-text {{
            color: #64748b;
            font-size: 14px;
            margin: 0;
        }}
        .brand {{
            font-weight: 700;
            color: #1e293b;
            font-size: 18px;
            margin-bottom: 8px;
        }}
        .alternative-link {{
            background-color: #f1f5f9;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            margin: 24px 0;
            font-size: 14px;
            color: #475569;
        }}
        .alternative-link a {{
            color: #2563eb;
            text-decoration: none;
            word-break: break-all;
        }}
        .alternative-link a:hover {{
            text-decoration: underline;
        }}
        @media (max-width: 640px) {{
            .container {{
                margin: 10px;
                border-radius: 8px;
            }}
            .header {{
                padding: 30px 20px;
            }}
            .header h1 {{
                font-size: 24px;
            }}
            .content {{
                padding: 30px 20px;
            }}
            .verify-button {{
                padding: 14px 28px;
                font-size: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 LIBRASYS</h1>
            <p>Verify Your Account</p>
        </div>

        <div class="content">
            <div class="greeting">Welcome, {full_name}!</div>

            <div class="message">
                Thank you for registering with LIBRASYS. To complete your registration and start borrowing books, please verify your email address by clicking the button below.
            </div>

            <div class="button-container">
                <a href="{verification_url}" class="verify-button" target="_blank" rel="noopener noreferrer">
                    ✅ Verify Email Address
                </a>
            </div>

            <div class="warning">
                <strong>⏰ Important:</strong> This verification link will expire in 24 hours for security reasons. If the link expires, you'll need to register again.
            </div>

            <div class="alternative-link">
                <strong>If the button doesn't work:</strong><br>
                Copy and paste this URL into your browser:<br>
                <a href="{verification_url}" target="_blank" rel="noopener noreferrer">{verification_url}</a>
            </div>

            <div class="message">
                If you did not request this registration, please ignore this email. Your email address will not be used without verification.
            </div>
        </div>

        <div class="footer">
            <div class="brand">LIBRASYS</div>
            <p class="footer-text">
                LIBRASYS - Library Management System<br>
                Secure • Reliable • Modern
            </p>
        </div>
    </div>
</body>
</html>
        """

        self.email_service.send_email(
            subject=subject,
            recipients=[email],
            body=body,
            html_body=html_body
        )


class VerifyEmailUseCase:
    """Use case for email verification"""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    def execute(self, token: str) -> dict:
        """
        Verify email using token

        Args:
            token: Verification token from email

        Returns:
            dict: Verification result
        """
        # Find registration request by token
        request = self.auth_service.student_repo.find_registration_request_by_token(token)
        if not request:
            raise ValueError("Invalid or expired verification token")

        # Check if token is expired (24 hours)
        created_at = request.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))

        if datetime.utcnow() - created_at > timedelta(hours=24):
            raise ValueError("Verification token has expired")

        # Mark email as verified
        self.auth_service.student_repo.update_registration_request_verified(token)

        return {
            'message': 'Email verified successfully. Your account is now pending admin approval.',
            'email': request.get('email'),
            'full_name': request.get('full_name')
        }


class ResendVerificationEmailUseCase:
    """Use case for resending verification email"""

    def __init__(self, auth_service: AuthService, email_service: EmailService):
        self.auth_service = auth_service
        self.email_service = email_service

    def execute(self, email: str) -> dict:
        """
        Resend verification email for pending registration

        Args:
            email: Email address

        Returns:
            dict: Result message
        """
        # Find pending registration request
        request = self.auth_service.student_repo.find_registration_request_by_email(email)
        if not request:
            raise ValueError("No pending registration request found for this email")

        if request.get('email_verified'):
            raise ValueError("Email is already verified")

        # Check if token is expired (24 hours)
        created_at = request.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))

        if datetime.utcnow() - created_at > timedelta(hours=24):
            # Generate new token for expired requests
            new_token = str(uuid.uuid4())
            self.auth_service.student_repo.update_registration_request_token(email, new_token)
            verification_token = new_token
        else:
            verification_token = request.get('verification_token')

        # Send verification email
        full_name = request.get('full_name')
        self._send_verification_email(email, full_name, verification_token)

        return {
            'message': 'Verification email sent successfully. Please check your email.',
            'email': email
        }

    def _send_verification_email(self, email: str, full_name: str, token: str):
        """Send email verification link"""
        verification_url = f"{Config.FRONTEND_URL}/verify-email?token={token}"

        subject = "Verify Your LIBRASYS Account"
        body = f"""
Dear {full_name},

Welcome to LIBRASYS! Thank you for registering with our library system.

To complete your registration and activate your account, please verify your email address by clicking the link below:

{verification_url}

This verification link will expire in 24 hours for security reasons.

If you did not request this registration, please ignore this email.

Best regards,
LIBRASYS Team
LIBRASYS
        """

        html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your LIBRASYS Account</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: #f8fafc;
            color: #334155;
            line-height: 1.6;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px 30px;
            text-align: center;
            color: white;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.025em;
        }}
        .header p {{
            margin: 8px 0 0 0;
            font-size: 16px;
            opacity: 0.9;
        }}
        .content {{
            padding: 40px 30px;
        }}
        .greeting {{
            font-size: 20px;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 16px;
        }}
        .message {{
            font-size: 16px;
            color: #64748b;
            margin-bottom: 32px;
            line-height: 1.7;
        }}
        .button-container {{
            text-align: center;
            margin: 40px 0;
        }}
        .verify-button {{
            display: inline-block;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            text-decoration: none;
            padding: 16px 32px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 16px;
            text-align: center;
            box-shadow: 0 4px 14px 0 rgba(16, 185, 129, 0.39);
            transition: all 0.2s ease;
            border: none;
            cursor: pointer;
        }}
        .verify-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px 0 rgba(16, 185, 129, 0.5);
        }}
        .warning {{
            background-color: #fef3c7;
            border: 1px solid #f59e0b;
            border-radius: 8px;
            padding: 16px;
            margin: 24px 0;
            font-size: 14px;
            color: #92400e;
        }}
        .warning strong {{
            color: #78350f;
        }}
        .footer {{
            background-color: #f8fafc;
            padding: 30px;
            text-align: center;
            border-top: 1px solid #e2e8f0;
        }}
        .footer-text {{
            color: #64748b;
            font-size: 14px;
            margin: 0;
        }}
        .brand {{
            font-weight: 700;
            color: #1e293b;
            font-size: 18px;
            margin-bottom: 8px;
        }}
        .alternative-link {{
            background-color: #f1f5f9;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            margin: 24px 0;
            font-size: 14px;
            color: #475569;
        }}
        .alternative-link a {{
            color: #2563eb;
            text-decoration: none;
            word-break: break-all;
        }}
        .alternative-link a:hover {{
            text-decoration: underline;
        }}
        @media (max-width: 640px) {{
            .container {{
                margin: 10px;
                border-radius: 8px;
            }}
            .header {{
                padding: 30px 20px;
            }}
            .header h1 {{
                font-size: 24px;
            }}
            .content {{
                padding: 30px 20px;
            }}
            .verify-button {{
                padding: 14px 28px;
                font-size: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 LIBRASYS</h1>
            <p>Verify Your Account</p>
        </div>

        <div class="content">
            <div class="greeting">Welcome, {full_name}!</div>

            <div class="message">
                Thank you for registering with LIBRASYS. To complete your registration and start borrowing books, please verify your email address by clicking the button below.
            </div>

            <div class="button-container">
                <a href="{verification_url}" class="verify-button" target="_blank" rel="noopener noreferrer">
                    ✅ Verify Email Address
                </a>
            </div>

            <div class="warning">
                <strong>⏰ Important:</strong> This verification link will expire in 24 hours for security reasons. If the link expires, you'll need to register again.
            </div>

            <div class="alternative-link">
                <strong>If the button doesn't work:</strong><br>
                Copy and paste this URL into your browser:<br>
                <a href="{verification_url}" target="_blank" rel="noopener noreferrer">{verification_url}</a>
            </div>

            <div class="message">
                If you did not request this registration, please ignore this email. Your email address will not be used without verification.
            </div>
        </div>

        <div class="footer">
            <div class="brand">LIBRASYS</div>
            <p class="footer-text">
                LIBRASYS - Library Management System<br>
                Secure • Reliable • Modern
            </p>
        </div>
    </div>
</body>
</html>
        """

        self.email_service.send_email(
            subject=subject,
            recipients=[email],
            body=body,
            html_body=html_body
        )


class ApproveRegistrationUseCase:
    """Use case for admin to approve student registration"""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    def execute(self, request_id: int, admin_email: str) -> dict:
        """
        Approve a student registration request

        Args:
            request_id: Registration request ID
            admin_email: Admin email performing the approval

        Returns:
            dict: Approval result
        """
        # Get registration request
        request = self.auth_service.student_repo.find_registration_request_by_id(request_id)
        if not request:
            raise ValueError("Registration request not found")

        if request.get('status') not in (None, 'pending'):
            raise ValueError("Only pending registration requests can be approved")

        if not request.get('email_verified'):
            raise ValueError("Email must be verified before approval")

        student_number = request.get('student_number')
        department = request.get('department')
        year_level = request.get('year_level')

        if not student_number:
            raise ValueError("Approved registration is missing Student ID")
        if not department:
            raise ValueError("Approved registration is missing Department / Program")
        if year_level is None:
            raise ValueError("Approved registration is missing Year Level")

        existing_student = self.auth_service.student_repo.find_student_by_student_number(student_number)
        if existing_student:
            raise ValueError("Student ID already registered")
        if self.auth_service.student_repo.find_student_by_email(request.get('email')):
            raise ValueError("Email already registered")

        # Create the student account
        student_id = self.auth_service.register_student(
            email=request.get('email'),
            full_name=request.get('full_name'),
            password_hash=request.get('password_hash'),
            student_number=student_number,
            status='active',
            email_verified=True,
            registration_document=request.get('registration_document'),
            department=department,
            year_level=year_level
        )

        # Update registration request status
        self.auth_service.student_repo.update_registration_request_status(request_id, 'approved')

        # Move the registration document to student uploads folder
        # (This would be handled by file storage service)

        return {
            'message': 'Student registration approved successfully',
            'student_id': student_id,
            'email': request.get('email')
        }
