from ....domain.services.auth_service import AuthService


class GetUserProfileUseCase:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    def execute(self, email: str, role: str = None):
        """
        Get user profile by email and optional role.
        
        Args:
            email: User email
            role: Optional role hint ('student', 'librarian', 'admin')
        
        Returns:
            User profile dictionary or None
        """
        return self.auth_service.get_profile(email, role)
