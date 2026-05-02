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
                student_id: str, registration_document) -> dict:
        """
        Execute secure student registration process

        Args:
            email: Student email
            full_name: Student full name
            password: Student password
            student_id: Student ID (format: STU2024001)
            registration_document: Uploaded file object

        Returns:
            dict: Registration result with message and request_id
        """
        # Sanitize inputs
        email = self.validation_service.sanitize_text(email)
        full_name = self.validation_service.sanitize_text(full_name)
        student_id = self.validation_service.sanitize_text(student_id)

        # Validate required fields
        valid, message = self.validation_service.validate_required_fields(
            email=email, full_name=full_name, password=password, student_id=student_id
        )
        if not valid:
            raise ValueError(message)

        # Validate email format and domain restrictions
        valid, message = self.validation_service.validate_email(email)
        if not valid:
            raise ValueError(message)

        # Validate student ID format
        if not self.validation_service.validate_student_id(student_id):
            raise ValueError("Invalid student ID format. Must be in format STU2024001")

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

        subject = "Verify Your Library Account"
        body = f"""
Dear {full_name},

Thank you for registering with NashLibrary!

To complete your registration, please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours for security reasons.

If you did not request this registration, please ignore this email.

Best regards,
NashLibrary Team
        """

        html_body = f"""
<html>
<body>
    <h2>Welcome to NashLibrary, {full_name}!</h2>
    <p>Thank you for registering with our library system.</p>
    <p>To complete your registration, please verify your email address by clicking the button below:</p>
    <p style="text-align: center; margin: 30px 0;">
        <a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">Verify Email Address</a>
    </p>
    <p><strong>Important:</strong> This link will expire in 24 hours for security reasons.</p>
    <p>If the button doesn't work, copy and paste this URL into your browser:</p>
    <p><a href="{verification_url}">{verification_url}</a></p>
    <p>If you did not request this registration, please ignore this email.</p>
    <br>
    <p>Best regards,<br>NashLibrary Team</p>
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

        if not request.get('email_verified'):
            raise ValueError("Email must be verified before approval")

        # Create the student account
        student_id = self.auth_service.register_student(
            email=request.get('email'),
            full_name=request.get('full_name'),
            password=request.get('password_hash'),  # This is already hashed
            student_number=request.get('student_number')
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
