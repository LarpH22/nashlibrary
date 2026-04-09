import pymysql

DB_NAME = 'library_system_v2'

conn = pymysql.connect(
    host='127.0.0.1',
    port=3307,
    user='root',
    password='',
    charset='utf8mb4'
)

try:
    with conn.cursor() as cur:
        # Drop the database
        cur.execute(f'DROP DATABASE IF EXISTS {DB_NAME}')
        print(f'Database {DB_NAME} has been dropped')
        
    conn.commit()
    
except Exception as e:
    print(f'Error: {e}')
finally:
    conn.close()
