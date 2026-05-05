import pymysql
from werkzeug.security import generate_password_hash
from backend.config import Config
import sys

def restore_accounts():
    """Restore all test accounts to the database"""
    
    try:
        conn = pymysql.connect(
            host=Config.DB_HOST,
            port=int(Config.DB_PORT),
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            cursorclass=pymysql.cursors.DictCursor,
            charset='utf8mb4'
        )
        
        with conn.cursor() as cur:
            # ===== ADMINS =====
            admin_password = generate_password_hash('admin123')
            cur.execute(
                'INSERT INTO admins (fullname, email, password, status) VALUES (%s, %s, %s, %s)',
                ('John Admin', 'admin@library.com', admin_password, 'active')
            )
            print('✓ Admin account created')
            
            # ===== LIBRARIANS =====
            lib_password = generate_password_hash('librarian123')
            cur.execute(
                'INSERT INTO librarians (fullname, email, password, employee_id, status) VALUES (%s, %s, %s, %s, %s)',
                ('Jane Librarian', 'librarian1@library.com', lib_password, 'LIB001', 'active')
            )
            print('✓ Librarian 1 account created')
            
            cur.execute(
                'INSERT INTO librarians (fullname, email, password, employee_id, status) VALUES (%s, %s, %s, %s, %s)',
                ('Mark Librarian', 'librarian2@library.com', lib_password, 'LIB002', 'active')
            )
            print('✓ Librarian 2 account created')
            
            # ===== STUDENTS =====
            student_password = generate_password_hash('student123')
            cur.execute(
                'INSERT INTO students (full_name, email, password_hash, student_number, department, year_level, status) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                ('Bob Student', 'student1@library.com', student_password, 'STU2024001', 'Computer Science', 3, 'active')
            )
            print('✓ Student 1 account created')
            
            cur.execute(
                'INSERT INTO students (full_name, email, password_hash, student_number, department, year_level, status) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                ('Alice Student', 'student2@library.com', student_password, 'STU2024002', 'Information Technology', 2, 'active')
            )
            print('✓ Student 2 account created')
            
            cur.execute(
                'INSERT INTO students (full_name, email, password_hash, student_number, department, year_level, status) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                ('Charlie Student', 'student3@library.com', student_password, 'STU2024003', 'Engineering', 1, 'active')
            )
            print('✓ Student 3 account created')
        
        conn.commit()
        print('\n✅ All test accounts have been successfully restored!')
        print('\n📋 Account Credentials:')
        print('  Admin: admin@library.com / admin123')
        print('  Librarian: librarian1@library.com / librarian123')
        print('  Librarian: librarian2@library.com / librarian123')
        print('  Student: student1@library.com / student123')
        print('  Student: student2@library.com / student123')
        print('  Student: student3@library.com / student123')
        
        conn.close()
        return True
        
    except pymysql.err.IntegrityError as e:
        if 'Duplicate entry' in str(e):
            print('⚠️  Some accounts already exist in the database.')
            print('   Run delete_all_accounts.py first if you want to clean slate restore.')
        else:
            print(f'❌ Database error: {e}')
        return False
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

if __name__ == '__main__':
    success = restore_accounts()
    sys.exit(0 if success else 1)
