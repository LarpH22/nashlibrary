import re

from flask import jsonify, request

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

        student_id = current_user.get('student_id')
        email = current_user.get('email')
        if student_id:
            profile_data = self.student_repo.get_student_profile_by_id(student_id)
        elif email:
            profile_data = self.get_profile_use_case.execute(email, 'student')
        else:
            return jsonify({'message': 'Student identity not present in token'}), 400
        if not profile_data:
            return jsonify({'message': 'Student not found'}), 404

        return jsonify(self._public_student_profile(profile_data)), 200

    def update_profile(self, current_user):
        if not current_user:
            return jsonify({'message': 'Authentication required'}), 401

        if current_user.get('role') != 'student':
            return jsonify({'message': 'Student access required'}), 403

        student_id = current_user.get('student_id')
        if not student_id:
            return jsonify({'message': 'Student ID not present in token'}), 400

        data = request.get_json(silent=True) or {}
        rejected_fields = sorted(set(data.keys()) - {'full_name', 'email'})
        if rejected_fields:
            return jsonify({'message': f"Fields not allowed: {', '.join(rejected_fields)}"}), 400

        allowed_payload = {
            key: data.get(key)
            for key in ['full_name', 'email']
            if key in data
        }
        if not allowed_payload:
            return jsonify({'message': 'No editable profile fields provided'}), 400

        validation_error = self._validate_profile_payload(allowed_payload, student_id)
        if validation_error:
            return jsonify({'message': validation_error}), 400

        self.student_repo.update_student_profile(student_id, allowed_payload)
        profile_data = self.student_repo.get_student_profile_by_id(student_id)
        if not profile_data:
            return jsonify({'message': 'Student not found'}), 404

        return jsonify({'message': 'Profile updated', 'profile': self._public_student_profile(profile_data)}), 200

    def _validate_profile_payload(self, payload, student_id):
        if 'full_name' in payload and not str(payload.get('full_name') or '').strip():
            return 'Full name is required'

        if 'email' in payload:
            email = str(payload.get('email') or '').strip().lower()
            if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
                return 'A valid email address is required'
            existing_student = self.student_repo.find_student_by_email(email)
            if existing_student and int(existing_student.get('student_id')) != int(student_id):
                return 'Email address is already in use'
            payload['email'] = email

        if 'department' in payload and not str(payload.get('department') or '').strip():
            return 'Department / Program is required'

        if 'year_level' in payload:
            try:
                year_level = int(payload.get('year_level'))
            except (TypeError, ValueError):
                return 'Year level must be a number'
            if year_level < 1 or year_level > 10:
                return 'Year level must be between 1 and 10'
            payload['year_level'] = year_level

        for key in ['full_name', 'department']:
            if key in payload:
                payload[key] = str(payload.get(key) or '').strip()

        return None

    def _public_student_profile(self, profile_data):
        student_number = profile_data.get('student_number')
        return {
            'student_id': student_number,
            'student_number': student_number,
            'internal_student_id': profile_data.get('student_id'),
            'full_name': profile_data.get('full_name'),
            'email': profile_data.get('email'),
            'department': profile_data.get('department'),
            'year_level': profile_data.get('year_level'),
            'last_login': profile_data.get('last_login'),
        }
