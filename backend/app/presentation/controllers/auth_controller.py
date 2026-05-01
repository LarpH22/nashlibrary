from datetime import datetime
import sys

from flask import jsonify, request, url_for
from flask_jwt_extended import create_access_token

from ...application.use_cases.user.create_user import CreateUserUseCase
from ...application.use_cases.user.login_user import LoginUserUseCase
from ...application.use_cases.user.get_user_profile import GetUserProfileUseCase
from ...domain.services.auth_service import AuthService
from ...infrastructure.repositories_impl.auth_repository_impl import (
    StudentAuthRepositoryImpl, LibrarianAuthRepositoryImpl, AdminAuthRepositoryImpl
)


class AuthController:
    def __init__(self):
        self.student_repo = StudentAuthRepositoryImpl()
        self.librarian_repo = LibrarianAuthRepositoryImpl()
        self.admin_repo = AdminAuthRepositoryImpl()
        self.auth_service = AuthService(self.student_repo, self.librarian_repo, self.admin_repo)
        self.create_user_use_case = CreateUserUseCase(self.auth_service)
        self.login_user_use_case = LoginUserUseCase(self.auth_service)
        self.get_profile_use_case = GetUserProfileUseCase(self.auth_service)

    def register(self):
        """Register a new user (student, librarian, or admin)"""
        data = request.get_json() or {}
        email = data.get('email')
        full_name = data.get('full_name')
        password = data.get('password')
        role = data.get('role', 'student')
        student_number = data.get('student_number')
        employee_id = data.get('employee_id')
        admin_level = data.get('admin_level', 'junior')

        if not email or not password or not full_name:
            return jsonify({'message': 'Email, full name, and password are required.'}), 400

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
