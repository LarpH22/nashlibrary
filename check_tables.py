#!/usr/bin/env python3
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
    for table in ['admins', 'librarians', 'students']:
        cur.execute(f'DESCRIBE {table}')
        cols = cur.fetchall()
        print(f'\n{table.upper()} columns:')
        for col in cols:
            print(f"  {col['Field']:30s} {col['Type']}")
conn.close()
