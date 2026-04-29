#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create admin and librarian accounts
"""

import pymysql
from dotenv import load_dotenv
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

load_dotenv()

DB_HOST = os.environ.get('DB_HOST') or '127.0.0.1'
DB_PORT = int(os.environ.get('DB_PORT', '3307'))
DB_USER = os.environ.get('DB_USER') or 'root'
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME') or 'library_system_v2'

def create_accounts():
    """Create admin and librarian accounts"""
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor,
            charset='utf8mb4'
        )
        
        with conn.cursor() as cur:
            print("\n" + "="*70)
            print("CREATING USER ACCOUNTS")
            print("="*70)
            
            # Create Admin Account
            print("\n[1/2] Creating Admin Account...")
            admin_email = "ralphrolandb30@gmail.com"
            admin_password = "Farmville"
            admin_password_hash = generate_password_hash(admin_password)
            
            try:
                cur.execute("""
                    INSERT INTO admins (admin_level, permissions, two_factor_enabled, 
                                       email, password_hash, full_name, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, ('super', '{}', False, admin_email, admin_password_hash, 
                      'Admin Account', 'active', datetime.now(), datetime.now()))
                print(f"  ✓ Admin account created")
                print(f"    Email: {admin_email}")
                print(f"    Password: {admin_password}")
            except pymysql.IntegrityError as e:
                print(f"  ✗ Admin account already exists or email conflict")
                return
            
            # Create Librarian Account
            print("\n[2/2] Creating Librarian Account...")
            librarian_email = "nashandreimonteiro@gmail.com"
            librarian_password = "Farmville2"
            librarian_password_hash = generate_password_hash(librarian_password)
            
            try:
                cur.execute("""
                    INSERT INTO librarians (employee_id, position, department, permissions,
                                          email, password_hash, full_name, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, ('LIB001', 'Head Librarian', 'Main Library', '{}', 
                      librarian_email, librarian_password_hash, 'Librarian Account', 
                      'active', datetime.now(), datetime.now()))
                print(f"  ✓ Librarian account created")
                print(f"    Email: {librarian_email}")
                print(f"    Password: {librarian_password}")
            except pymysql.IntegrityError as e:
                print(f"  ✗ Librarian account already exists or email conflict")
                return
            
            conn.commit()
            
            # Display all accounts
            print("\n" + "="*70)
            print("CURRENT ACCOUNTS IN SYSTEM")
            print("="*70)
            
            cur.execute("SELECT admin_id as id, email, full_name, 'ADMIN' as role FROM admins ORDER BY admin_id")
            admins = cur.fetchall()
            print("\nADMIN ACCOUNTS:")
            for admin in admins:
                print(f"  ID: {admin['id']:2d} | {admin['email']:35s} | {admin['full_name']}")
            
            cur.execute("SELECT librarian_id as id, email, full_name, 'LIBRARIAN' as role FROM librarians ORDER BY librarian_id")
            librarians = cur.fetchall()
            print("\nLIBRARIAN ACCOUNTS:")
            for lib in librarians:
                print(f"  ID: {lib['id']:2d} | {lib['email']:35s} | {lib['full_name']}")
            
            cur.execute("SELECT student_id as id, email, full_name, 'STUDENT' as role FROM students ORDER BY student_id")
            students = cur.fetchall()
            print("\nSTUDENT ACCOUNTS:")
            for student in students:
                print(f"  ID: {student['id']:2d} | {student['email']:35s} | {student['full_name']}")
            
            print("\n" + "="*70)
            print("✓ All accounts created successfully!")
            print("="*70 + "\n")
        
        conn.close()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_accounts()
