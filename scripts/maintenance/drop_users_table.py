import pymysql

DB_NAME = 'library_system_v2'

conn = pymysql.connect(
    host='127.0.0.1',
    port=3307,
    user='root',
    password='',
    database=DB_NAME,
    charset='utf8mb4'
)

try:
    with conn.cursor() as cur:
        # Disable foreign key checks to avoid constraint violations
        cur.execute('SET FOREIGN_KEY_CHECKS=0')
        
        # Drop the users table
        cur.execute('DROP TABLE IF EXISTS users')
        print('Users table has been dropped')
        
        # Re-enable foreign key checks
        cur.execute('SET FOREIGN_KEY_CHECKS=1')
        
        # Show remaining tables
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema=%s", (DB_NAME,))
        tables = cur.fetchall()
        print(f'\nRemaining tables in {DB_NAME}:')
        for table in tables:
            print(f'  - {table[0]}')
        
    conn.commit()
    print('\nUsers table successfully removed!')
    
except Exception as e:
    print(f'Error: {e}')
finally:
    conn.close()
