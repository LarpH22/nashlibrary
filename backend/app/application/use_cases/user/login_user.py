from ....domain.services.auth_service import AuthService


class LoginUserUseCase:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    def execute(self, email: str, password: str, role: str = None):
        """
        Authenticate a user.
        
        Args:
            email: User email
            password: User password
            role: Optional role hint ('student', 'librarian', 'admin')
        
        Returns:
            Tuple of (user_data, role) on success, (None, None) on failure
        """
        return self.auth_service.authenticate(email, password, role)
