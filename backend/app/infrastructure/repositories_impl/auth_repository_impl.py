from ..database.db_connection import get_connection
from ...domain.repositories.auth_repository import StudentAuthRepository, LibrarianAuthRepository, AdminAuthRepository


class StudentAuthRepositoryImpl(StudentAuthRepository):
    """Student authentication repository implementation"""

    def create_student(self, email: str, full_name: str, password_hash: str,
                       student_number: str | None = None, status: str = 'pending',
                       email_verified: bool = False,
                       registration_document: str | None = None,
                       department: str | None = None,
                       year_level: int | None = None,
                       verification_token: str | None = None):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO students
                       (email, full_name, password_hash, student_number, status,
                        email_verified, registration_document, department, year_level,
                        verification_token, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())""",
                    (
                        email,
                        full_name,
                        password_hash,
                        student_number,
                        status,
                        email_verified,
                        registration_document,
                        department,
                        year_level,
                        verification_token,
                    )
                )
                conn.commit()
                return cur.lastrowid

    def find_student_by_email(self, email: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM students WHERE email=%s LIMIT 1", (email,))
                return cur.fetchone()

    def find_student_by_id(self, student_id: int):
        with get_connection() as conn:
            self._ensure_student_profile_columns(conn)
            conn.commit()
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM students WHERE student_id=%s LIMIT 1", (student_id,))
                return cur.fetchone()

    def find_student_by_student_number(self, student_number: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM students WHERE student_number=%s LIMIT 1", (student_number,))
                return cur.fetchone()

    def get_student_profile(self, email: str):
        with get_connection() as conn:
            self._ensure_student_profile_columns(conn)
            conn.commit()
        student = self.find_student_by_email(email)
        return self._student_profile_response(student)

    def get_student_profile_by_id(self, student_id: int):
        student = self.find_student_by_id(student_id)
        return self._student_profile_response(student)

    def _student_profile_response(self, student):
        if not student:
            return None
        return {
            'student_id': student.get('student_id'),
            'user_id': student.get('student_id'),
            'email': student.get('email'),
            'full_name': student.get('full_name'),
            'student_number': student.get('student_number'),
            'department': student.get('department'),
            'year_level': student.get('year_level'),
            'last_login': student.get('last_login'),
            'role': 'student'
        }

    def update_student_profile(self, student_id: int, profile_data: dict):
        allowed_fields = {
            'full_name': profile_data.get('full_name'),
            'email': profile_data.get('email'),
        }
        updates = []
        params = []
        for field, value in allowed_fields.items():
            if value is not None:
                updates.append(f"{field}=%s")
                params.append(value)

        if not updates:
            return False

        params.append(student_id)
        with get_connection() as conn:
            self._ensure_student_profile_columns(conn)
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE students SET {', '.join(updates)}, updated_at=NOW() WHERE student_id=%s",
                    tuple(params),
                )
                conn.commit()
                return cur.rowcount > 0

    def update_student_last_login(self, student_id: int):
        with get_connection() as conn:
            self._ensure_student_profile_columns(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE students SET last_login=NOW(), updated_at=NOW() WHERE student_id=%s",
                    (student_id,),
                )
                conn.commit()
                return cur.rowcount > 0

    def _ensure_student_profile_columns(self, conn):
        with conn.cursor() as cur:
            if not self._column_exists(cur, 'students', 'department'):
                cur.execute("ALTER TABLE students ADD COLUMN department VARCHAR(30) NULL")
            if not self._column_exists(cur, 'students', 'year_level'):
                cur.execute("ALTER TABLE students ADD COLUMN year_level INT NULL")
            if not self._column_exists(cur, 'students', 'last_login'):
                cur.execute("ALTER TABLE students ADD COLUMN last_login TIMESTAMP NULL")
            if not self._column_exists(cur, 'students', 'updated_at'):
                cur.execute(
                    "ALTER TABLE students ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
                )

    def _column_exists(self, cur, table_name, column_name):
        cur.execute(
            """
            SELECT COUNT(*) AS count
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = %s
              AND column_name = %s
            """,
            (table_name, column_name),
        )
        return cur.fetchone()['count'] > 0

    def update_student_status(self, email: str, status: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE students SET status=%s, updated_at=NOW() WHERE email=%s",
                    (status, email)
                )
                conn.commit()
                return cur.rowcount > 0

    def update_student_password(self, student_id: int, password_hash: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE students SET password_hash=%s, updated_at=NOW() WHERE student_id=%s",
                    (password_hash, student_id)
                )
                conn.commit()
                return cur.rowcount > 0

    def create_registration_request(self, email: str, full_name: str, password_hash: str,
                                   student_number: str, registration_document: str,
                                   verification_token: str,
                                   department: str | None = None,
                                   year_level: int | None = None):
        with get_connection() as conn:
            with conn.cursor() as cur:
                if not self._column_exists(cur, 'registration_requests', 'student_number'):
                    cur.execute("ALTER TABLE registration_requests ADD COLUMN student_number VARCHAR(20) NULL")
                if not self._column_exists(cur, 'registration_requests', 'department'):
                    cur.execute("ALTER TABLE registration_requests ADD COLUMN department VARCHAR(30) NULL")
                if not self._column_exists(cur, 'registration_requests', 'year_level'):
                    cur.execute("ALTER TABLE registration_requests ADD COLUMN year_level INT NULL")
                cur.execute(
                    """INSERT INTO registration_requests
                       (email, full_name, password_hash, student_number, registration_document,
                        department, year_level, verification_token, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())""",
                    (email, full_name, password_hash, student_number, registration_document,
                     department, year_level, verification_token)
                )
                conn.commit()
                return cur.lastrowid

    def find_registration_request_by_email(self, email: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM registration_requests
                    WHERE email=%s
                      AND (status IS NULL OR status='pending')
                    LIMIT 1
                    """,
                    (email,),
                )
                return cur.fetchone()

    def find_registration_request_by_student_number(self, student_number: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM registration_requests
                    WHERE student_number=%s
                      AND (status IS NULL OR status='pending')
                    LIMIT 1
                    """,
                    (student_number,),
                )
                return cur.fetchone()

    def find_registration_request_by_token(self, token: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM registration_requests WHERE verification_token=%s LIMIT 1", (token,))
                return cur.fetchone()

    def find_registration_request_by_id(self, request_id: int):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM registration_requests WHERE request_id=%s LIMIT 1", (request_id,))
                return cur.fetchone()

    def update_registration_request_verified(self, token: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE registration_requests SET email_verified=TRUE, verified_at=NOW() WHERE verification_token=%s",
                    (token,)
                )
                conn.commit()
                return cur.rowcount > 0

    def update_registration_request_token(self, email: str, new_token: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE registration_requests SET verification_token=%s, created_at=NOW() WHERE email=%s",
                    (new_token, email)
                )
                conn.commit()
                return cur.rowcount > 0

    def update_registration_request_status(self, request_id: int, status: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE registration_requests SET status=%s WHERE request_id=%s",
                    (status, request_id)
                )
                conn.commit()
                return cur.rowcount > 0

    def update_student_reset_token(self, student_id: int, reset_token: str, reset_expires_at):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE students SET reset_token=%s, reset_expires_at=%s WHERE student_id=%s",
                    (reset_token, reset_expires_at, student_id)
                )
                conn.commit()
                return cur.rowcount > 0

    def find_student_by_reset_token(self, reset_token: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM students WHERE reset_token=%s LIMIT 1", (reset_token,))
                return cur.fetchone()

    def update_student_password_and_clear_token(self, student_id: int, password_hash: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE students 
                       SET password_hash=%s, reset_token=NULL, reset_expires_at=NULL, updated_at=NOW() 
                       WHERE student_id=%s""",
                    (password_hash, student_id)
                )
                conn.commit()
                return cur.rowcount > 0


class LibrarianAuthRepositoryImpl(LibrarianAuthRepository):
    """Librarian authentication repository implementation"""
    
    def create_librarian(self, email: str, full_name: str, password_hash: str, 
                        employee_id: str, status: str = 'active'):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO librarians 
                       (email, full_name, password_hash, employee_id, status, created_at) 
                       VALUES (%s, %s, %s, %s, %s, NOW())""",
                    (email, full_name, password_hash, employee_id, status)
                )
                conn.commit()
                return cur.lastrowid

    def find_librarian_by_email(self, email: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM librarians WHERE email=%s LIMIT 1", (email,))
                return cur.fetchone()

    def get_librarian_profile(self, email: str):
        librarian = self.find_librarian_by_email(email)
        if not librarian:
            return None
        return {
            'librarian_id': librarian.get('librarian_id'),
            'email': librarian.get('email'),
            'full_name': librarian.get('full_name'),
            'employee_id': librarian.get('employee_id'),
            'position': librarian.get('position'),
            'department': librarian.get('department'),
            'status': librarian.get('status'),
            'role': 'librarian'
        }

    def update_librarian_status(self, email: str, status: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE librarians SET status=%s, updated_at=NOW() WHERE email=%s",
                    (status, email)
                )
                conn.commit()
                return cur.rowcount > 0


class AdminAuthRepositoryImpl(AdminAuthRepository):
    """Admin authentication repository implementation"""
    
    def create_admin(self, email: str, full_name: str, password_hash: str, 
                    admin_level: str = 'junior', status: str = 'active'):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO admins 
                       (email, full_name, password_hash, admin_level, status, created_at) 
                       VALUES (%s, %s, %s, %s, %s, NOW())""",
                    (email, full_name, password_hash, admin_level, status)
                )
                conn.commit()
                return cur.lastrowid

    def find_admin_by_email(self, email: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM admins WHERE email=%s LIMIT 1", (email,))
                return cur.fetchone()

    def get_admin_profile(self, email: str):
        admin = self.find_admin_by_email(email)
        if not admin:
            return None
        return {
            'admin_id': admin.get('admin_id'),
            'email': admin.get('email'),
            'full_name': admin.get('full_name'),
            'admin_level': admin.get('admin_level'),
            'status': admin.get('status'),
            'role': 'admin'
        }

    def update_admin_status(self, email: str, status: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE admins SET status=%s, updated_at=NOW() WHERE email=%s",
                    (status, email)
                )
                conn.commit()
                return cur.rowcount > 0
