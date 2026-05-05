import pymysql

conn = pymysql.connect(
    host='127.0.0.1',
    port=3307,
    user='root',
    password='',
    database='library_system_v2',
    charset='utf8mb4'
)

try:
    with conn.cursor() as cur:
        cur.execute('SELECT email, full_name FROM students LIMIT 10')
        rows = cur.fetchall()
        print("Students in database:")
        for row in rows:
            print(f"  Email: {row[0]}, Name: {row[1]}")
        
        # Also check admins and librarians
        cur.execute('SELECT email, full_name FROM admins LIMIT 5')
        rows = cur.fetchall()
        print("\nAdmins in database:")
        for row in rows:
            print(f"  Email: {row[0]}, Name: {row[1]}")
            
        cur.execute('SELECT email, full_name FROM librarians LIMIT 5')
        rows = cur.fetchall()
        print("\nLibrarians in database:")
        for row in rows:
            print(f"  Email: {row[0]}, Name: {row[1]}")
        
finally:
    conn.close()
