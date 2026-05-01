from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from ...application.use_cases.user.get_user_profile import GetUserProfileUseCase
from ...domain.services.auth_service import AuthService
from ...infrastructure.repositories_impl.auth_repository_impl import (
    StudentAuthRepositoryImpl, LibrarianAuthRepositoryImpl, AdminAuthRepositoryImpl
)


class UserController:
    def __init__(self):
        self.student_repo = StudentAuthRepositoryImpl()
        self.librarian_repo = LibrarianAuthRepositoryImpl()
        self.admin_repo = AdminAuthRepositoryImpl()
        self.auth_service = AuthService(self.student_repo, self.librarian_repo, self.admin_repo)
        self.get_profile_use_case = GetUserProfileUseCase(self.auth_service)

    def profile(self):
        jwt_identity = get_jwt_identity()
        
        # Handle both old format (just email string) and new format (dict with email and role)
        if isinstance(jwt_identity, dict):
            email = jwt_identity.get('email')
            role = jwt_identity.get('role')
        else:
            email = jwt_identity
            role = None
        
        profile = self.get_profile_use_case.execute(email, role)
        if not profile:
            return jsonify({'message': 'User not found'}), 404
        return jsonify(profile), 200
