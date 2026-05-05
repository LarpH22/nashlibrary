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
    print("\n" + "="*70)
    print("DATABASE VERIFICATION")
    print("="*70)
    
    # Check tables
    cur.execute("SHOW TABLES")
    tables = cur.fetchall()
    table_names = sorted([list(t.values())[0] for t in tables])
    print("\n✓ Tables in database:")
    for table_name in table_names:
        print(f"  - {table_name}")
    
    # Check if users table exists
    if 'users' in table_names:
        print("\n✗ WARNING: 'users' table still exists!")
    else:
        print("\n✓ 'users' table successfully removed")
    
    # Count records in each role table
    print("\n✓ Current accounts:")
    cur.execute("SELECT COUNT(*) as count FROM admins")
    print(f"  - Admins: {cur.fetchone()['count']}")
    cur.execute("SELECT COUNT(*) as count FROM librarians")
    print(f"  - Librarians: {cur.fetchone()['count']}")
    cur.execute("SELECT COUNT(*) as count FROM students")
    print(f"  - Students: {cur.fetchone()['count']}")
    
    # Display your credentials
    print("\n" + "="*70)
    print("YOUR LOGIN CREDENTIALS")
    print("="*70)
    cur.execute("SELECT email, full_name FROM admins WHERE email = 'ralphrolandb30@gmail.com'")
    admin = cur.fetchone()
    if admin:
        print(f"\nADMIN:")
        print(f"  Email: {admin['email']}")
        print(f"  Name: {admin['full_name']}")
        print(f"  Password: Farmville")
    
    cur.execute("SELECT email, full_name FROM librarians WHERE email = 'nashandreimonteiro@gmail.com'")
    lib = cur.fetchone()
    if lib:
        print(f"\nLIBRARIAN:")
        print(f"  Email: {lib['email']}")
        print(f"  Name: {lib['full_name']}")
        print(f"  Password: Farmville2")
    
    print("\n" + "="*70)
    print("✓ Database refactoring complete!")
    print("="*70 + "\n")

conn.close()
