from flask import jsonify

from ...application.use_cases.user.get_user_profile import GetUserProfileUseCase
from ...domain.services.auth_service import AuthService
from ...infrastructure.repositories_impl.auth_repository_impl import (
    StudentAuthRepositoryImpl, LibrarianAuthRepositoryImpl, AdminAuthRepositoryImpl
)


class StudentController:
    def __init__(self):
        self.student_repo = StudentAuthRepositoryImpl()
        self.librarian_repo = LibrarianAuthRepositoryImpl()
        self.admin_repo = AdminAuthRepositoryImpl()
        self.auth_service = AuthService(self.student_repo, self.librarian_repo, self.admin_repo)
        self.get_profile_use_case = GetUserProfileUseCase(self.auth_service)

    def profile(self, current_user):
        if not current_user:
            return jsonify({'message': 'Authentication required'}), 401

        if current_user.get('role') != 'student':
            return jsonify({'message': 'Student access required'}), 403

        email = current_user.get('email')
        if not email:
            return jsonify({'message': 'Student email not present in token'}), 400

        profile_data = self.get_profile_use_case.execute(email, 'student')
        if not profile_data:
            return jsonify({'message': 'Student not found'}), 404

        return jsonify(profile_data), 200
