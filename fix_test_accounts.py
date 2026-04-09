import pymysql
from werkzeug.security import generate_password_hash
from datetime import datetime
from backend.config import Config

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

# Delete old accounts
conn = get_connection()
with conn.cursor() as cur:
    cur.execute("SET FOREIGN_KEY_CHECKS=0")
    cur.execute("DELETE FROM audit_logs WHERE user_id IN (SELECT user_id FROM users WHERE email LIKE '%library.com')")
    cur.execute("DELETE FROM students WHERE user_id IN (SELECT user_id FROM users WHERE email LIKE '%library.com')")
    cur.execute("DELETE FROM librarians WHERE user_id IN (SELECT user_id FROM users WHERE email LIKE '%library.com')")
    cur.execute("DELETE FROM admins WHERE user_id IN (SELECT user_id FROM users WHERE email LIKE '%library.com')")
    cur.execute("DELETE FROM users WHERE email LIKE '%library.com'")
    cur.execute("SET FOREIGN_KEY_CHECKS=1")
conn.commit()
conn.close()

print('Deleted old test accounts')

# Create new accounts with proper hashing
accounts = [
    {'full_name': 'John Admin', 'email': 'admin@library.com', 'password': 'admin123', 'role': 'admin'},
    {'full_name': 'Jane Librarian', 'email': 'librarian1@library.com', 'password': 'librarian123', 'role': 'librarian'},
    {'full_name': 'Mark Librarian', 'email': 'librarian2@library.com', 'password': 'librarian123', 'role': 'librarian'},
    {'full_name': 'General User', 'email': 'user1@library.com', 'password': 'user123', 'role': 'user'},
    {'full_name': 'Bob Student', 'email': 'student1@library.com', 'password': 'student123', 'role': 'student'},
    {'full_name': 'Alice Student', 'email': 'student2@library.com', 'password': 'student123', 'role': 'student'},
    {'full_name': 'Charlie Student', 'email': 'student3@library.com', 'password': 'student123', 'role': 'student'}
]

conn = get_connection()
with conn.cursor() as cur:
    for user in accounts:
        hashed = generate_password_hash(user['password'], method='pbkdf2:sha256')
        print(f"Creating {user['email']} with hash prefix: {hashed[:20]}...")
        
        cur.execute(
            'INSERT INTO users (full_name, email, password_hash, role, status, created_at) VALUES (%s,%s,%s,%s,%s,%s)',
            (user['full_name'], user['email'], hashed, user['role'], 'active', datetime.utcnow())
        )
        user_id = cur.lastrowid
        
        if user['role'] == 'student':
            cur.execute('INSERT INTO students (user_id, student_number) VALUES (%s,%s)', (user_id, f'STU{user_id:05d}'))
        elif user['role'] == 'librarian':
            cur.execute('INSERT INTO librarians (user_id, employee_id) VALUES (%s,%s)', (user_id, f'LIB{user_id:05d}'))
        elif user['role'] == 'admin':
            cur.execute('INSERT INTO admins (user_id, admin_level) VALUES (%s,%s)', (user_id, 'super'))
    
    conn.commit()

print('✓ Test accounts recreated with proper password hashing!')
conn.close()
