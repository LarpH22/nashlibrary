#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration: Remove users table and merge user data into admin/librarian/student tables
"""

import pymysql
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

DB_HOST = os.environ.get('DB_HOST') or '127.0.0.1'
DB_PORT = int(os.environ.get('DB_PORT', '3307'))
DB_USER = os.environ.get('DB_USER') or 'root'
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME') or 'library_system_v2'

def run_migration():
    """Execute the migration"""
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
            print("MIGRATION: Removing Users Table")
            print("="*70)
            
            # Step 1: Disable foreign key checks
            print("\n[1/9] Disabling foreign key checks...")
            cur.execute("SET FOREIGN_KEY_CHECKS=0")
            
            # Step 2: Add user columns to admins table
            print("[2/9] Adding user columns to admins table...")
            columns_to_add = [
                "email VARCHAR(100) UNIQUE NOT NULL",
                "password_hash VARCHAR(255) NOT NULL",
                "full_name VARCHAR(100) NOT NULL",
                "phone VARCHAR(20)",
                "address TEXT",
                "status ENUM('active', 'inactive', 'suspended') DEFAULT 'active'",
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
                "last_login TIMESTAMP NULL"
            ]
            
            for col_def in columns_to_add:
                col_name = col_def.split()[0]
                try:
                    cur.execute(f"ALTER TABLE admins ADD COLUMN {col_def}")
                    print(f"  ✓ Added {col_name}")
                except:
                    pass  # Column might already exist
            
            # Step 3: Add user columns to librarians table
            print("[3/9] Adding user columns to librarians table...")
            for col_def in columns_to_add:
                col_name = col_def.split()[0]
                try:
                    cur.execute(f"ALTER TABLE librarians ADD COLUMN {col_def}")
                    print(f"  ✓ Added {col_name}")
                except:
                    pass
            
            # Step 4: Add user columns to students table
            print("[4/9] Adding user columns to students table...")
            for col_def in columns_to_add:
                col_name = col_def.split()[0]
                try:
                    cur.execute(f"ALTER TABLE students ADD COLUMN {col_def}")
                    print(f"  ✓ Added {col_name}")
                except:
                    pass
            
            # Step 5: Migrate admin data
            print("[5/9] Migrating admin data from users table...")
            cur.execute("""
                UPDATE admins a
                JOIN users u ON a.user_id = u.user_id
                SET a.email = u.email,
                    a.password_hash = u.password_hash,
                    a.full_name = u.full_name,
                    a.phone = u.phone,
                    a.address = u.address,
                    a.status = u.status,
                    a.created_at = u.created_at,
                    a.updated_at = u.updated_at,
                    a.last_login = u.last_login
                WHERE u.role = 'admin'
            """)
            print(f"  ✓ Migrated {cur.rowcount} admin records")
            
            # Step 6: Migrate librarian data
            print("[6/9] Migrating librarian data from users table...")
            cur.execute("""
                UPDATE librarians l
                JOIN users u ON l.user_id = u.user_id
                SET l.email = u.email,
                    l.password_hash = u.password_hash,
                    l.full_name = u.full_name,
                    l.phone = u.phone,
                    l.address = u.address,
                    l.status = u.status,
                    l.created_at = u.created_at,
                    l.updated_at = u.updated_at,
                    l.last_login = u.last_login
                WHERE u.role = 'librarian'
            """)
            print(f"  ✓ Migrated {cur.rowcount} librarian records")
            
            # Step 7: Migrate student data
            print("[7/9] Migrating student data from users table...")
            cur.execute("""
                UPDATE students s
                JOIN users u ON s.user_id = u.user_id
                SET s.email = u.email,
                    s.password_hash = u.password_hash,
                    s.full_name = u.full_name,
                    s.phone = u.phone,
                    s.address = u.address,
                    s.status = u.status,
                    s.created_at = u.created_at,
                    s.updated_at = u.updated_at,
                    s.last_login = u.last_login
                WHERE u.role = 'student'
            """)
            print(f"  ✓ Migrated {cur.rowcount} student records")
            
            # Step 8: Update foreign keys - remove user_id from the three role tables
            print("[8/9] Cleaning up foreign keys...")
            try:
                cur.execute("ALTER TABLE admins DROP FOREIGN KEY admins_ibfk_1")
                cur.execute("ALTER TABLE admins DROP COLUMN user_id")
                print("  ✓ Removed user_id from admins")
            except:
                pass
            
            try:
                cur.execute("ALTER TABLE librarians DROP FOREIGN KEY librarians_ibfk_1")
                cur.execute("ALTER TABLE librarians DROP COLUMN user_id")
                print("  ✓ Removed user_id from librarians")
            except:
                pass
            
            try:
                cur.execute("ALTER TABLE students DROP FOREIGN KEY students_ibfk_1")
                cur.execute("ALTER TABLE students DROP COLUMN user_id")
                print("  ✓ Removed user_id from students")
            except:
                pass
            
            # Step 9: Drop users table
            print("[9/9] Dropping users table...")
            cur.execute("DROP TABLE IF EXISTS users")
            print("  ✓ Dropped users table")
            
            # Re-enable foreign key checks
            cur.execute("SET FOREIGN_KEY_CHECKS=1")
            
            conn.commit()
            print("\n" + "="*70)
            print("✓ Migration completed successfully!")
            print("="*70 + "\n")
        
        conn.close()
        
    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_migration()
