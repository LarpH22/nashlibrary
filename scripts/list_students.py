#!/usr/bin/env python3
"""List all students in the database"""

import mysql.connector
from mysql.connector import Error

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='nashlibrary'
    )
    
    cur = conn.cursor(dictionary=True)
    
    cur.execute('SELECT student_id, email, full_name, student_number, department, year_level, status FROM students ORDER BY student_id LIMIT 50')
    students = cur.fetchall()
    
    if not students:
        print("No students found in database")
    else:
        print(f"Found {len(students)} students:\n")
        print(f"{'ID':<5} {'Student #':<15} {'Name':<30} {'Email':<35} {'Dept':<20} {'Status':<10}")
        print("-" * 120)
        for s in students:
            print(f"{s['student_id']:<5} {s['student_number']:<15} {s['full_name']:<30} {s['email']:<35} {s['department']:<20} {s['status']:<10}")
    
    cur.close()
    conn.close()
    
except Error as e:
    print(f"Error: {e}")
    exit(1)
