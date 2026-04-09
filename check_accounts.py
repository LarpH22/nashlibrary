import pymysql
import sys
sys.path.insert(0, '.')
from backend.config import Config

try:
    conn = pymysql.connect(
        host=Config.DB_HOST,
        port=int(Config.DB_PORT),
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )
    with conn.cursor() as cur:
        cur.execute('SELECT user_id, email, full_name, role, status FROM users')
        users = cur.fetchall()
        print('Users in database:')
        for user in users:
            print(f"  ID: {user['user_id']}, Email: {user['email']}, Name: {user['full_name']}, Role: {user['role']}, Status: {user['status']}")
    conn.close()
except Exception as e:
    print(f'Error: {e}')
