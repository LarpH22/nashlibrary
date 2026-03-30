import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    charset='utf8mb4'
)

try:
    with conn.cursor() as cur:
        # Drop the database
        cur.execute('DROP DATABASE IF EXISTS library_system')
        print('✓ Database library_system has been dropped')
        
    conn.commit()
    
except Exception as e:
    print(f'Error: {e}')
finally:
    conn.close()
