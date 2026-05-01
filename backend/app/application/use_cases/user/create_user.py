from datetime import datetime

from ....domain.services.auth_service import AuthService


class CreateUserUseCase:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    def execute(self, email: str, full_name: str, password: str, 
               role: str = 'student', student_number: str | None = None, 
               employee_id: str | None = None, admin_level: str = 'junior'):
        """
        Create a new user based on role.
        
        Args:
            email: User email
            full_name: User full name
            password: User password (will be hashed)
            role: 'student', 'librarian', or 'admin'
            student_number: Required for students
            employee_id: Required for librarians
            admin_level: Optional for admins (default 'junior')
        """
        if role == 'student':
            return self.auth_service.register_student(
                email=email,
                full_name=full_name,
                password=password,
                student_number=student_number,
            )
        elif role == 'librarian':
            if not employee_id:
                raise ValueError('employee_id is required for librarian registration')
            return self.auth_service.register_librarian(
                email=email,
                full_name=full_name,
                password=password,
                employee_id=employee_id,
            )
        elif role == 'admin':
            return self.auth_service.register_admin(
                email=email,
                full_name=full_name,
                password=password,
                admin_level=admin_level,
            )
        else:
            raise ValueError(f'Invalid role: {role}. Must be student, librarian, or admin.')
