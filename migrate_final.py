#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Migration: Clean up and remove users table
"""

import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.environ.get('DB_HOST') or '127.0.0.1'
DB_PORT = int(os.environ.get('DB_PORT', '3307'))
DB_USER = os.environ.get('DB_USER') or 'root'
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME') or 'library_system_v2'

def run_migration():
    """Execute the final migration"""
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
            print("FINAL MIGRATION: Cleanup")
            print("="*70)
            
            # Disable foreign key checks
            print("\n[1/7] Disabling foreign key checks...")
            cur.execute("SET FOREIGN_KEY_CHECKS=0")
            
            # Add email columns properly (nullable first)
            print("[2/7] Adding email columns (nullable)...")
            try:
                cur.execute("ALTER TABLE librarians ADD COLUMN IF NOT EXISTS email VARCHAR(100) AFTER permissions")
                print("  ✓ Email column ready for librarians")
            except:
                pass
            
            try:
                cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS email VARCHAR(100) AFTER proof_file")
                print("  ✓ Email column ready for students")
            except:
                pass
            
            # Migrate data from users table
            print("[3/7] Migrating data from users table...")
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
            
            # Drop foreign keys from admins, librarians, students
            print("[4/7] Removing foreign key constraints...")
            try:
                cur.execute("ALTER TABLE admins DROP FOREIGN KEY admins_ibfk_1")
                print("  ✓ Removed FK from admins")
            except:
                pass
            
            try:
                cur.execute("ALTER TABLE librarians DROP FOREIGN KEY librarians_ibfk_1")
                print("  ✓ Removed FK from librarians")
            except:
                pass
            
            try:
                cur.execute("ALTER TABLE students DROP FOREIGN KEY students_ibfk_1")
                print("  ✓ Removed FK from students")
            except:
                pass
            
            # Drop user_id columns
            print("[5/7] Removing user_id columns...")
            try:
                cur.execute("ALTER TABLE admins DROP COLUMN user_id")
                print("  ✓ Removed user_id from admins")
            except:
                pass
            
            try:
                cur.execute("ALTER TABLE librarians DROP COLUMN user_id")
                print("  ✓ Removed user_id from librarians")
            except:
                pass
            
            try:
                cur.execute("ALTER TABLE students DROP COLUMN user_id")
                print("  ✓ Removed user_id from students")
            except:
                pass
            
            # Drop users table
            print("[6/7] Dropping users table...")
            cur.execute("DROP TABLE IF EXISTS users")
            print("  ✓ Dropped users table")
            
            # Re-enable foreign key checks
            cur.execute("SET FOREIGN_KEY_CHECKS=1")
            
            conn.commit()
            
            # Verify
            print("[7/7] Verifying final schema...")
            cur.execute("SHOW TABLES")
            tables = cur.fetchall()
            table_names = sorted([list(t.values())[0] for t in tables])
            print("\n" + "="*70)
            print("✓ Migration completed! Remaining tables:")
            print("="*70)
            for table_name in table_names:
                print(f"  - {table_name}")
            print("="*70 + "\n")
        
        conn.close()
        
    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_migration()
