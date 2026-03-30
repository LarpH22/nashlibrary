import pymysql
from werkzeug.security import generate_password_hash

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database='library_system',
    cursorclass=pymysql.cursors.DictCursor,
    charset='utf8mb4'
)

try:
    with conn.cursor() as cur:
        # Clear existing data in correct order
        cur.execute('DELETE FROM audit_logs')
        cur.execute('DELETE FROM fines')
        cur.execute('DELETE FROM borrow_records')
        cur.execute('DELETE FROM books')
        cur.execute('DELETE FROM admins')
        cur.execute('DELETE FROM librarians')
        cur.execute('DELETE FROM students')
        cur.execute('DELETE FROM users')
        
        # Create admin account
        admin_hash = generate_password_hash('admin123')
        cur.execute(
            'INSERT INTO users (email, password_hash, full_name, phone, role, status) VALUES (%s, %s, %s, %s, %s, %s)',
            ('admin@library.com', admin_hash, 'John Admin', '+1234567890', 'admin', 'active')
        )
        admin_id = cur.lastrowid
        cur.execute('INSERT INTO admins (user_id, admin_level) VALUES (%s, %s)', (admin_id, 'super'))
        
        # Create librarian accounts
        librarian_hash1 = generate_password_hash('librarian123')
        cur.execute(
            'INSERT INTO users (email, password_hash, full_name, phone, role, status) VALUES (%s, %s, %s, %s, %s, %s)',
            ('librarian1@library.com', librarian_hash1, 'Jane Librarian', '+1234567891', 'librarian', 'active')
        )
        lib_id1 = cur.lastrowid
        cur.execute('INSERT INTO librarians (user_id, employee_id, position) VALUES (%s, %s, %s)', (lib_id1, 'LIB001', 'Senior Librarian'))
        
        librarian_hash2 = generate_password_hash('librarian123')
        cur.execute(
            'INSERT INTO users (email, password_hash, full_name, phone, role, status) VALUES (%s, %s, %s, %s, %s, %s)',
            ('librarian2@library.com', librarian_hash2, 'Mark Librarian', '+1234567892', 'librarian', 'active')
        )
        lib_id2 = cur.lastrowid
        cur.execute('INSERT INTO librarians (user_id, employee_id, position) VALUES (%s, %s, %s)', (lib_id2, 'LIB002', 'Junior Librarian'))
        
        # Create student accounts
        student_hash1 = generate_password_hash('student123')
        cur.execute(
            'INSERT INTO users (email, password_hash, full_name, phone, role, status) VALUES (%s, %s, %s, %s, %s, %s)',
            ('student1@library.com', student_hash1, 'Bob Student', '+1234567893', 'student', 'active')
        )
        stu_id1 = cur.lastrowid
        cur.execute('INSERT INTO students (user_id, student_number, department, year_level) VALUES (%s, %s, %s, %s)', 
                   (stu_id1, 'STU2024001', 'Computer Science', 3))
        
        student_hash2 = generate_password_hash('student123')
        cur.execute(
            'INSERT INTO users (email, password_hash, full_name, phone, role, status) VALUES (%s, %s, %s, %s, %s, %s)',
            ('student2@library.com', student_hash2, 'Alice Student', '+1234567894', 'student', 'active')
        )
        stu_id2 = cur.lastrowid
        cur.execute('INSERT INTO students (user_id, student_number, department, year_level) VALUES (%s, %s, %s, %s)', 
                   (stu_id2, 'STU2024002', 'Information Technology', 2))
        
    conn.commit()
    print('✓ Test accounts created with valid passwords:')
    print('  Admin: admin@library.com / admin123')
    print('  Librarian: librarian1@library.com / librarian123')
    print('  Student: student1@library.com / student123')
    
except Exception as e:
    print(f'Error: {e}')
finally:
    conn.close()
