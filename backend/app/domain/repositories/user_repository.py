from abc import ABC, abstractmethod


class UserRepository(ABC):
    @abstractmethod
    def create_user(self, email: str, full_name: str, password_hash: str, role: str = 'student', status: str = 'pending', student_number: str | None = None):
        raise NotImplementedError

    @abstractmethod
    def find_by_email(self, email: str):
        raise NotImplementedError

    @abstractmethod
    def get_profile(self, email: str):
        raise NotImplementedError
