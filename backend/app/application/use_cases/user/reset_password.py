from datetime import datetime

from ....domain.services.auth_service import AuthService


class ResetPasswordUseCase:
    """Use case for handling password reset with token validation"""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    def execute(self, token: str, new_password: str) -> dict:
        """
        Execute password reset process

        Args:
            token: Reset token from email link
            new_password: New password to set

        Returns:
            dict: Success message

        Raises:
            ValueError: If token is invalid, expired, or password reset fails
        """
        # Find student with matching reset token
        student = self.auth_service.student_repo.find_student_by_reset_token(token)
        if not student:
            raise ValueError("Invalid reset token")

        # Check if token has expired
        reset_expires = student.get('reset_expires_at')
        if not reset_expires or datetime.fromisoformat(str(reset_expires)) < datetime.utcnow():
            raise ValueError("Reset token has expired. Please request a new password reset.")

        # Hash the new password
        hashed_password = self.auth_service.hash_password(new_password)

        # Update student password and clear reset token
        self.auth_service.student_repo.update_student_password_and_clear_token(
            student['student_id'], hashed_password
        )

        return {'message': 'Password reset successfully'}
