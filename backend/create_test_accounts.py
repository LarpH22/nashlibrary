import pymysql
from werkzeug.security import generate_password_hash
from datetime import datetime
import sys
import os

# Handle imports for both execution contexts
try:
    from backend.config import Config
except ImportError:
    from config import Config


def get_connection():
    return pymysql.connect(
        host=Config.DB_HOST,
        port=int(Config.DB_PORT),
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        charset='utf8mb4'
    )


def create_test_accounts():
    accounts = [
        {'full_name': 'John Admin', 'email': 'admin@library.com', 'password': 'admin123', 'role': 'admin'},
        {'full_name': 'Jane Librarian', 'email': 'librarian1@library.com', 'password': 'librarian123', 'role': 'librarian'},
        {'full_name': 'Mark Librarian', 'email': 'librarian2@library.com', 'password': 'librarian123', 'role': 'librarian'},
        {'full_name': 'Bob Student', 'email': 'student1@library.com', 'password': 'student123', 'role': 'student'},
        {'full_name': 'Alice Student', 'email': 'student2@library.com', 'password': 'student123', 'role': 'student'},
        {'full_name': 'Charlie Student', 'email': 'student3@library.com', 'password': 'student123', 'role': 'student'}
    ]

    with get_connection() as conn:
        with conn.cursor() as cur:
            for user in accounts:
                cur.execute('SELECT user_id FROM users WHERE email=%s', (user['email'],))
                if cur.fetchone():
                    continue

                hashed = generate_password_hash(user['password'])
                cur.execute(
                    'INSERT INTO users (full_name, email, password_hash, role, status, created_at) VALUES (%s,%s,%s,%s,%s,%s)',
                    (user['full_name'], user['email'], hashed, user['role'], 'active', datetime.utcnow())
                )
                user_id = cur.lastrowid

                if user['role'] == 'student':
                    cur.execute('INSERT INTO students (user_id, student_number) VALUES (%s,%s)', (user_id, f'STU{user_id:05d}'))
                elif user['role'] == 'librarian':
                    cur.execute('INSERT INTO librarians (user_id, employee_id) VALUES (%s,%s)', (user_id, f'LIB{user_id:05d}'))

        conn.commit()

    print('Test accounts created successfully')


if __name__ == '__main__':
    create_test_accounts()
