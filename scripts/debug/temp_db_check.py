import pymysql
import os
from dotenv import load_dotenv

load_dotenv()
conn = pymysql.connect(
    host=os.environ.get('DB_HOST', '127.0.0.1'),
    port=int(os.environ.get('DB_PORT', 3307)),
    user=os.environ.get('DB_USER', 'root'),
    password=os.environ.get('DB_PASSWORD'),
    database=os.environ.get('DB_NAME', 'library_system_v2'),
    cursorclass=pymysql.cursors.DictCursor
)
with conn.cursor() as cur:
    cur.execute('DESCRIBE admins')
    print('admins columns:')
    for row in cur.fetchall():
        print(' ', row['Field'], row['Type'])
    cur.execute('DESCRIBE librarians')
    print('librarians columns:')
    for row in cur.fetchall():
        print(' ', row['Field'], row['Type'])
    cur.execute('DESCRIBE students')
    print('students columns:')
    for row in cur.fetchall():
        print(' ', row['Field'], row['Type'])
    try:
        cur.execute("SELECT *, 'admin' AS role FROM admins WHERE email=%s OR full_name=%s", ('ralphrolandb30@gmail.com','ralphrolandb30@gmail.com'))
        print('admins login query result:', cur.fetchone())
    except Exception as e:
        print('admins query error:', e)
    try:
        cur.execute("SELECT *, 'librarian' AS role FROM librarians WHERE email=%s OR full_name=%s", ('nashandreimonteiro@gmail.com','nashandreimonteiro@gmail.com'))
        print('librarians login query result:', cur.fetchone())
    except Exception as e:
        print('librarians query error:', e)
conn.close()
