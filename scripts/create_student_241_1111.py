#!/usr/bin/env python3
"""Create test student 241-1111 for testing"""

import mysql.connector
from mysql.connector import Error
import bcrypt

def hash_password(password):
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='nashlibrary'
    )
    
    cur = conn.cursor(dictionary=True)
    
    # Check if student already exists
    cur.execute('SELECT * FROM students WHERE student_number=%s', ('241-1111',))
    if cur.fetchone():
        print("Student 241-1111 already exists")
        cur.close()
        conn.close()
        exit(0)
    
    # Create new student
    password_hash = hash_password('student123')
    cur.execute('''
        INSERT INTO students 
        (email, password_hash, full_name, student_number, department, year_level, status, email_verified)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        'student_241_1111@library.com',
        password_hash,
        'Test Student 241-1111',
        '241-1111',
        'Computer Science',
        2,
        'active',
        True
    ))
    
    conn.commit()
    print(f"Created student 241-1111 successfully")
    
    # Verify
    cur.execute('SELECT student_id, email, student_number, full_name FROM students WHERE student_number=%s', ('241-1111',))
    student = cur.fetchone()
    print(f"Verified: {student}")
    
    cur.close()
    conn.close()
    
except Error as e:
    print(f"Error: {e}")
    exit(1)
