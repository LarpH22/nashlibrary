from ..database.db_connection import get_connection
from ...domain.repositories.user_repository import UserRepository


class UserRepositoryImpl(UserRepository):
    def create_user(self, email: str, full_name: str, password_hash: str, role: str = 'student', status: str = 'pending', student_number: str | None = None):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (email, full_name, password_hash, role, status, student_number, created_at) VALUES (%s, %s, %s, %s, %s, %s, NOW())",
                    (email, full_name, password_hash, role, status, student_number)
                )
                conn.commit()
                return cur.lastrowid

    def find_by_email(self, email: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE email=%s LIMIT 1", (email,))
                return cur.fetchone()

    def get_profile(self, email: str):
        user = self.find_by_email(email)
        if not user:
            return None
        return {
            'email': user.get('email'),
            'full_name': user.get('full_name'),
            'role': user.get('role'),
            'status': user.get('status'),
            'student_number': user.get('student_number')
        }
