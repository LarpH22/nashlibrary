import pymysql
from werkzeug.security import generate_password_hash
from backend.config import Config

conn = pymysql.connect(
    host=Config.DB_HOST,
    port=int(Config.DB_PORT),
    user=Config.DB_USER,
    password=Config.DB_PASSWORD,
    database=Config.DB_NAME,
    charset='utf8mb4'
)

try:
    with conn.cursor() as cur:
        # Update admin password
        admin_hash = generate_password_hash('admin123')
        cur.execute('UPDATE users SET password_hash=%s WHERE email=%s', (admin_hash, 'admin@library.com'))
        
        # Update librarian passwords
        librarian_hash = generate_password_hash('librarian123')
        cur.execute('UPDATE users SET password_hash=%s WHERE email IN (%s, %s)', (librarian_hash, 'librarian1@library.com', 'librarian2@library.com'))
        
        # Update student passwords
        student_hash = generate_password_hash('student123')
        cur.execute('UPDATE users SET password_hash=%s WHERE email IN (%s, %s, %s)', (student_hash, 'student1@library.com', 'student2@library.com', 'student3@library.com'))
        
    conn.commit()
    print('✓ All test account passwords reset successfully:')
    print('  Admin: admin@library.com / admin123')
    print('  Librarian: librarian@library.com / librarian123')
    print('  Student: student@library.com / student123')
    
except Exception as e:
    print(f'Error: {e}')
finally:
    conn.close()
