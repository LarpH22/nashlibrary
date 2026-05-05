import pymysql
from werkzeug.security import generate_password_hash
from backend.config import Config

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
        # Restore Admin Account
        admin_password = generate_password_hash('Farmville')
        cur.execute(
            'INSERT INTO admins (fullname, email, password, status) VALUES (%s, %s, %s, %s)',
            ('Ralph Roland B', 'ralphrolandb30@gmail.com', admin_password, 'active')
        )
        print('✓ Admin account restored: ralphrolandb30@gmail.com')
        
        # Update Librarian Account password
        lib_password = generate_password_hash('Farmville2')
        cur.execute(
            'UPDATE librarians SET password = %s WHERE email = %s',
            (lib_password, 'nashandreimonteiro@gmail.com')
        )
        print('✓ Librarian account password updated: nashandreimonteiro@gmail.com')
        
    conn.commit()
    print('\n✅ Accounts successfully restored!')
    print('\nRestored Credentials:')
    print('  Admin: ralphrolandb30@gmail.com / Farmville')
    print('  Librarian: nashandreimonteiro@gmail.com / Farmville2')
    
    conn.close()
except pymysql.err.IntegrityError as e:
    if 'Duplicate entry' in str(e):
        print('⚠️  Admin account already exists. Updating password...')
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
            admin_password = generate_password_hash('Farmville')
            cur.execute(
                'UPDATE admins SET password = %s WHERE email = %s',
                (admin_password, 'ralphrolandb30@gmail.com')
            )
        conn.commit()
        print('✓ Admin password updated: ralphrolandb30@gmail.com')
        conn.close()
    else:
        print(f'Error: {e}')
except Exception as e:
    print(f'Error: {e}')
