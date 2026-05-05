import pymysql
import bcrypt

# Connect to database
conn = pymysql.connect(
    host='127.0.0.1',
    port=3307,
    user='root',
    password='',
    database='library_system_v2'
)

cursor = conn.cursor()

# Generate hashes
student_hash = bcrypt.hashpw(b'student123', bcrypt.gensalt()).decode('utf-8')
librarian_hash = bcrypt.hashpw(b'librarian123', bcrypt.gensalt()).decode('utf-8')
admin_hash = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')

print(f"student hash: {student_hash}")
print(f"librarian hash: {librarian_hash}")
print(f"admin hash: {admin_hash}")

# Update students
cursor.execute("UPDATE students SET password_hash = %s WHERE email IN ('student1@library.com', 'student2@library.com', 'student3@library.com')", (student_hash,))

# Update librarians
cursor.execute("UPDATE librarians SET password_hash = %s WHERE email IN ('librarian1@library.com', 'librarian2@library.com')", (librarian_hash,))

# Update admins
cursor.execute("UPDATE admins SET password_hash = %s WHERE email = 'admin@library.com'", (admin_hash,))

conn.commit()
print("Updated all passwords!")
conn.close()
