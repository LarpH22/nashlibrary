import logging

from flask import g
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt, get_jwt_identity

from ...infrastructure.repositories_impl.auth_repository_impl import StudentAuthRepositoryImpl

jwt_manager = JWTManager()
logger = logging.getLogger(__name__)


def set_current_user():
    """Validate JWT and attach current user info to flask.g."""
    verify_jwt_in_request()
    claims = get_jwt()
    identity = get_jwt_identity()

    current_user = {
        'email': identity if isinstance(identity, str) else identity.get('email'),
        'role': claims.get('role'),
        'student_id': claims.get('student_id'),
        'librarian_id': claims.get('librarian_id'),
        'admin_id': claims.get('admin_id')
    }

    if current_user.get('role') == 'student' and not current_user.get('student_id'):
        email = current_user.get('email')
        if email:
            try:
                profile = StudentAuthRepositoryImpl().get_student_profile(email)
                if profile and profile.get('student_id'):
                    current_user['student_id'] = profile.get('student_id')
                    current_user.setdefault('full_name', profile.get('full_name'))
                    current_user.setdefault('student_number', profile.get('student_number'))
                    current_user.setdefault('department', profile.get('department'))
                    current_user.setdefault('year_level', profile.get('year_level'))
                    current_user.setdefault('status', profile.get('status'))
                    current_user.setdefault('email_verified', profile.get('email_verified'))
                else:
                    logger.warning(
                        'Authenticated student email=%s did not resolve to a student profile or student_id',
                        email
                    )
            except Exception as exc:
                logger.exception('Failed to fetch student record for email=%s during auth middleware', email)

    g.current_user = current_user
    return current_user
