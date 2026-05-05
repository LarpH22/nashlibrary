import pymysql
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
        print('=== ADMIN ACCOUNTS ===')
        cur.execute('SELECT id, fullname, email, status FROM admins')
        for row in cur.fetchall():
            print(f"  {row['fullname']} ({row['email']}) - {row['status']}")
        
        print('\n=== LIBRARIAN ACCOUNTS ===')
        cur.execute('SELECT id, fullname, email, employee_id, status FROM librarians')
        for row in cur.fetchall():
            print(f"  {row['fullname']} ({row['email']}) - Employee ID: {row['employee_id']} - {row['status']}")
            
        print('\n=== STUDENT ACCOUNTS ===')
        cur.execute('SELECT student_id, full_name, email, student_number, status FROM students')
        for row in cur.fetchall():
            print(f"  {row['full_name']} ({row['email']}) - Student #: {row['student_number']} - {row['status']}")
            
    conn.close()
except Exception as e:
    print(f'Error: {e}')
