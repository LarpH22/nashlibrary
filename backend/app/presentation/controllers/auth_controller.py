from datetime import datetime
import sys

from flask import jsonify, request, url_for
from flask_jwt_extended import create_access_token

from ...application.use_cases.user.create_user import CreateUserUseCase
from ...application.use_cases.user.secure_student_registration import (
    SecureStudentRegistrationUseCase, VerifyEmailUseCase, ApproveRegistrationUseCase
)
from ...application.use_cases.user.login_user import LoginUserUseCase
from ...application.use_cases.user.get_user_profile import GetUserProfileUseCase
from ...domain.services.auth_service import AuthService
from ...domain.services.validation_service import ValidationService
from ...infrastructure.repositories_impl.auth_repository_impl import (
    StudentAuthRepositoryImpl, LibrarianAuthRepositoryImpl, AdminAuthRepositoryImpl
)
from ...infrastructure.external.email_service import EmailService
from ...infrastructure.external.file_storage import FileStorage
from ...infrastructure.config import Config


class AuthController:
    def __init__(self):
        self.student_repo = StudentAuthRepositoryImpl()
        self.librarian_repo = LibrarianAuthRepositoryImpl()
        self.admin_repo = AdminAuthRepositoryImpl()
        self.auth_service = AuthService(self.student_repo, self.librarian_repo, self.admin_repo)
        self.validation_service = ValidationService()

        # Initialize external services
        self.email_service = EmailService()
        self.file_storage = FileStorage(
            upload_folder=Config.UPLOAD_FOLDER,
            allowed_extensions=Config.ALLOWED_EXTENSIONS
        )

        # Initialize use cases
        self.create_user_use_case = CreateUserUseCase(self.auth_service)
        self.login_user_use_case = LoginUserUseCase(self.auth_service)
        self.get_profile_use_case = GetUserProfileUseCase(self.auth_service)
        self.secure_student_registration_use_case = SecureStudentRegistrationUseCase(
            self.auth_service, self.email_service, self.file_storage, self.validation_service
        )
        self.verify_email_use_case = VerifyEmailUseCase(self.auth_service)
        self.approve_registration_use_case = ApproveRegistrationUseCase(self.auth_service)

    def register(self):
        """Register a new user (student, librarian, or admin)"""
        # Check if it's a student registration with file upload
        if 'registration_document' in request.files:
            return self._register_student_secure()
        else:
            return self._register_other_users()

    def _register_student_secure(self):
        """Secure student registration with file upload and email verification"""
        try:
            email = request.form.get('email')
            full_name = request.form.get('full_name')
            password = request.form.get('password')
            student_id = request.form.get('student_id')
            registration_document = request.files.get('registration_document')

            result = self.secure_student_registration_use_case.execute(
                email=email,
                full_name=full_name,
                password=password,
                student_id=student_id,
                registration_document=registration_document
            )

            return jsonify(result), 201

        except ValueError as e:
            return jsonify({'message': str(e)}), 400
        except Exception as e:
            return jsonify({'message': 'Registration failed', 'error': str(e)}), 500

    def _register_other_users(self):
        """Register librarians and admins (admin only, no email verification needed)"""
        data = request.get_json(silent=True) or {}
        if not data and request.form:
            data = request.form.to_dict(flat=True)

        email = data.get('email')
        full_name = data.get('full_name')
        password = data.get('password')
        role = data.get('role', 'student')
        student_number = data.get('student_number')
        employee_id = data.get('employee_id')
        admin_level = data.get('admin_level', 'junior')

        if not email or not password or not full_name:
            return jsonify({'message': 'Email, full name, and password are required.'}), 400

        # Only allow librarian and admin registration through this endpoint
        if role not in ['librarian', 'admin']:
            return jsonify({'message': 'This endpoint is for librarian and admin registration only. Use student registration for students.'}), 400

        try:
            user_id = self.create_user_use_case.execute(
                email=email,
                full_name=full_name,
                password=password,
                role=role,
                student_number=student_number,
                employee_id=employee_id,
                admin_level=admin_level
            )
            return jsonify({
                'message': f'{role.capitalize()} registration successful',
                'user_id': user_id,
                'role': role
            }), 201
        except ValueError as e:
            return jsonify({'message': str(e)}), 400
        except Exception as e:
            return jsonify({'message': str(e)}), 400

    def verify_email(self):
        """Verify email using token from email link"""
        try:
            token = request.args.get('token')
            if not token:
                return jsonify({'message': 'Verification token is required'}), 400

            result = self.verify_email_use_case.execute(token)
            return jsonify(result), 200

        except ValueError as e:
            return jsonify({'message': str(e)}), 400
        except Exception as e:
            return jsonify({'message': 'Email verification failed', 'error': str(e)}), 500

    def approve_registration(self):
        """Admin endpoint to approve student registration"""
        try:
            data = request.get_json() or {}
            request_id = data.get('request_id')
            admin_email = data.get('admin_email')  # From JWT token in real implementation

            if not request_id:
                return jsonify({'message': 'Request ID is required'}), 400

            result = self.approve_registration_use_case.execute(request_id, admin_email)
            return jsonify(result), 200

        except ValueError as e:
            return jsonify({'message': str(e)}), 400
        except Exception as e:
            return jsonify({'message': 'Registration approval failed', 'error': str(e)}), 500

    def login(self):
        """Authenticate a user"""
        print("Login called")
        data = request.get_json() or {}
        print("Data:", data)
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')  # Optional role hint

        print("Email:", email, "Password:", password, "Role:", role)
        user, auth_role = self.login_user_use_case.execute(email, password, role)
        print("User:", user, "Role:", auth_role)
        if not user:
            return jsonify({'message': 'Invalid credentials'}), 401

        # Create JWT token with role information
        token_data = {
            'email': user['email'],
            'role': auth_role
        }
        if auth_role == 'student' and 'student_id' in user:
            token_data['student_id'] = user['student_id']
        elif auth_role == 'librarian' and 'librarian_id' in user:
            token_data['librarian_id'] = user['librarian_id']
        elif auth_role == 'admin' and 'admin_id' in user:
            token_data['admin_id'] = user['admin_id']

        additional_claims = token_data
        token = create_access_token(identity=user['email'], additional_claims=additional_claims)
        
        return jsonify({
            'access_token': token,
            'role': auth_role,
            'email': user['email'],
            'full_name': user.get('full_name')
        }), 200

    def profile(self):
        """Get the profile of the authenticated user using JWT identity."""
        raise NotImplementedError('Use JWT identity from get_jwt_identity() in routes')
