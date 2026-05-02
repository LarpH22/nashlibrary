import bcrypt
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

from ..repositories.auth_repository import StudentAuthRepository, LibrarianAuthRepository, AdminAuthRepository


class AuthService:
    """Authentication service supporting three independent user types"""
    
    def __init__(self, student_repo: StudentAuthRepository, 
                 librarian_repo: LibrarianAuthRepository,
                 admin_repo: AdminAuthRepository):
        self.student_repo = student_repo
        self.librarian_repo = librarian_repo
        self.admin_repo = admin_repo

    def hash_password(self, password: str) -> str:
        """Hash password using Werkzeug (compatible with legacy passwords)"""
        return generate_password_hash(password, method='pbkdf2:sha256')

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password - handles both legacy and new hash formats"""
        try:
            # Try Werkzeug format first (handles both legacy and new passwords)
            return check_password_hash(hashed_password, password)
        except Exception:
            # Fallback to bcrypt if Werkzeug fails
            try:
                return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
            except Exception:
                return False

    def register_student(self, email: str, full_name: str, password: str, 
                        student_number: str | None = None):
        """Register a new student"""
        password_hash = self.hash_password(password)
        return self.student_repo.create_student(
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            student_number=student_number,
            status='pending',
        )

    def register_librarian(self, email: str, full_name: str, password: str, 
                          employee_id: str):
        """Register a new librarian (admin only)"""
        password_hash = self.hash_password(password)
        return self.librarian_repo.create_librarian(
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            employee_id=employee_id,
            status='active',
        )

    def register_admin(self, email: str, full_name: str, password: str, 
                      admin_level: str = 'junior'):
        """Register a new admin (super admin only)"""
        password_hash = self.hash_password(password)
        return self.admin_repo.create_admin(
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            admin_level=admin_level,
            status='active',
        )

    def authenticate_student(self, email: str, password: str):
        """Authenticate a student"""
        user = self.student_repo.find_student_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.get('password_hash', '')):
            return None
        # Check if email is verified and account is active
        if not user.get('email_verified', False):
            return None
        if user.get('status') != 'active':
            return None
        return user

    def authenticate_librarian(self, email: str, password: str):
        """Authenticate a librarian"""
        user = self.librarian_repo.find_librarian_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.get('password_hash', '')):
            return None
        return user

    def authenticate_admin(self, email: str, password: str):
        """Authenticate an admin"""
        user = self.admin_repo.find_admin_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.get('password_hash', '')):
            return None
        return user

    def authenticate(self, email: str, password: str, role: str = None):
        """
        Authenticate a user by role.
        If role is not specified, try all roles.
        Returns (user, role) tuple on success, (None, None) on failure.
        """
        if role == 'student':
            user = self.authenticate_student(email, password)
            return (user, 'student') if user else (None, None)
        elif role == 'librarian':
            user = self.authenticate_librarian(email, password)
            return (user, 'librarian') if user else (None, None)
        elif role == 'admin':
            user = self.authenticate_admin(email, password)
            return (user, 'admin') if user else (None, None)
        else:
            # Try all roles
            user = self.authenticate_student(email, password)
            if user:
                return (user, 'student')
            user = self.authenticate_librarian(email, password)
            if user:
                return (user, 'librarian')
            user = self.authenticate_admin(email, password)
            if user:
                return (user, 'admin')
            return (None, None)

    def get_profile(self, email: str, role: str = None):
        """Get user profile by email and optional role"""
        if role == 'student':
            return self.student_repo.get_student_profile(email)
        elif role == 'librarian':
            return self.librarian_repo.get_librarian_profile(email)
        elif role == 'admin':
            return self.admin_repo.get_admin_profile(email)
        else:
            # Try all roles
            profile = self.student_repo.get_student_profile(email)
            if profile:
                return profile
            profile = self.librarian_repo.get_librarian_profile(email)
            if profile:
                return profile
            profile = self.admin_repo.get_admin_profile(email)
            if profile:
                return profile
            return None
