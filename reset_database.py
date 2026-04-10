import pymysql
from backend.config import Config

conn = pymysql.connect(
    host=Config.DB_HOST,
    port=int(Config.DB_PORT),
    user=Config.DB_USER,
    password=Config.DB_PASSWORD,
    cursorclass=pymysql.cursors.DictCursor,
    charset='utf8mb4'
)

try:
    with conn.cursor() as cur:
        # Drop the entire database
        cur.execute(f'DROP DATABASE IF EXISTS {Config.DB_NAME}')
        print(f'✓ Dropped database {Config.DB_NAME}')
        
        # Recreate it
        cur.execute(f'CREATE DATABASE {Config.DB_NAME}')
        print(f'✓ Created fresh database {Config.DB_NAME}')
        
    conn.commit()
    print('\n✓ Database reset complete. Now run:')
    print('  1. python import_schema.py')
    print('  2. python create_test_users.py')
except Exception as e:
    print(f'Error: {e}')
finally:
    conn.close()
