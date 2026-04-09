import pymysql
from backend.config import Config

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
    cur.execute("SELECT email, role, status FROM users WHERE email='user1@library.com'")
    user = cur.fetchone()
    print(user)
conn.close()
