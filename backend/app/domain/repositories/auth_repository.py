from abc import ABC, abstractmethod


class StudentAuthRepository(ABC):
    """Student authentication repository interface"""
    
    @abstractmethod
    def create_student(self, email: str, full_name: str, password_hash: str, 
                       student_number: str | None = None, status: str = 'pending'):
        raise NotImplementedError

    @abstractmethod
    def find_student_by_email(self, email: str):
        raise NotImplementedError

    @abstractmethod
    def get_student_profile(self, email: str):
        raise NotImplementedError

    @abstractmethod
    def update_student_status(self, email: str, status: str):
        raise NotImplementedError


class LibrarianAuthRepository(ABC):
    """Librarian authentication repository interface"""
    
    @abstractmethod
    def create_librarian(self, email: str, full_name: str, password_hash: str, 
                        employee_id: str, status: str = 'active'):
        raise NotImplementedError

    @abstractmethod
    def find_librarian_by_email(self, email: str):
        raise NotImplementedError

    @abstractmethod
    def get_librarian_profile(self, email: str):
        raise NotImplementedError

    @abstractmethod
    def update_librarian_status(self, email: str, status: str):
        raise NotImplementedError


class AdminAuthRepository(ABC):
    """Admin authentication repository interface"""
    
    @abstractmethod
    def create_admin(self, email: str, full_name: str, password_hash: str, 
                    admin_level: str = 'junior', status: str = 'active'):
        raise NotImplementedError

    @abstractmethod
    def find_admin_by_email(self, email: str):
        raise NotImplementedError

    @abstractmethod
    def get_admin_profile(self, email: str):
        raise NotImplementedError

    @abstractmethod
    def update_admin_status(self, email: str, status: str):
        raise NotImplementedError
