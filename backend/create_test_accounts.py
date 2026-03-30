import pymysql
from werkzeug.security import generate_password_hash
from backend.config import Config
from datetime import datetime


def get_connection():
    return pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        charset='utf8mb4'
    )


def create_test_accounts():
    accounts = [
        {'full_name': 'Student One', 'email': 'student1@test.com', 'password': 'pass123', 'role': 'student'},
        {'full_name': 'Librarian One', 'email': 'librarian1@test.com', 'password': 'pass123', 'role': 'librarian'},
        {'full_name': 'Admin One', 'email': 'admin1@test.com', 'password': 'pass123', 'role': 'admin'}
    ]

    with get_connection() as conn:
        with conn.cursor() as cur:
            for user in accounts:
                cur.execute('SELECT user_id FROM users WHERE email=%s', (user['email'],))
                if cur.fetchone():
                    continue

                hashed = generate_password_hash(user['password'])
                cur.execute(
                    'INSERT INTO users (full_name, email, password, role, created_at) VALUES (%s,%s,%s,%s,%s)',
                    (user['full_name'], user['email'], hashed, user['role'], datetime.utcnow())
                )
                user_id = cur.lastrowid

                if user['role'] == 'student':
                    cur.execute('INSERT INTO students (user_id) VALUES (%s)', (user_id,))
                elif user['role'] == 'librarian':
                    cur.execute('INSERT INTO librarians (user_id) VALUES (%s)', (user_id,))

        conn.commit()

    print('Test accounts created successfully')


if __name__ == '__main__':
    create_test_accounts()
