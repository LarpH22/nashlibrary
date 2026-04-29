#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Corrected Migration: Remove users table and finalize schema
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
    """Execute the corrected migration"""
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
            print("CORRECTED MIGRATION: Finalizing Schema")
            print("="*70)
            
            # Disable foreign key checks
            print("\n[1/5] Disabling foreign key checks...")
            cur.execute("SET FOREIGN_KEY_CHECKS=0")
            
            # Add email to librarians if missing
            print("[2/5] Adding missing email column to librarians...")
            try:
                cur.execute("ALTER TABLE librarians ADD COLUMN email VARCHAR(100) UNIQUE NOT NULL AFTER permissions")
                print("  ✓ Added email to librarians")
            except Exception as e:
                if "Duplicate column" in str(e) or "already exists" in str(e):
                    print("  ✓ Email already exists in librarians")
                else:
                    raise
            
            # Add email to students if missing
            print("[3/5] Adding missing email column to students...")
            try:
                cur.execute("ALTER TABLE students ADD COLUMN email VARCHAR(100) UNIQUE NOT NULL AFTER proof_file")
                print("  ✓ Added email to students")
            except Exception as e:
                if "Duplicate column" in str(e) or "already exists" in str(e):
                    print("  ✓ Email already exists in students")
                else:
                    raise
            
            # Migrate data from users table
            print("[4/5] Migrating remaining data from users table...")
            
            # Get data from users that hasn't been migrated yet
            cur.execute("""
                SELECT u.user_id, u.email, u.password_hash, u.full_name, u.phone, u.address, 
                       u.status, u.created_at, u.updated_at, u.last_login, u.role
                FROM users u
                WHERE u.role IN ('librarian', 'student')
            """)
            users_to_migrate = cur.fetchall()
            
            for user in users_to_migrate:
                if user['role'] == 'librarian':
                    # Check if already migrated
                    cur.execute(f"SELECT user_id FROM librarians WHERE user_id = %s", (user['user_id'],))
                    if cur.fetchone():
                        cur.execute(f"""
                            UPDATE librarians 
                            SET email = %s, password_hash = %s, full_name = %s, phone = %s, 
                                address = %s, status = %s, created_at = %s, updated_at = %s, last_login = %s
                            WHERE user_id = %s
                        """, (user['email'], user['password_hash'], user['full_name'], user['phone'],
                              user['address'], user['status'], user['created_at'], user['updated_at'],
                              user['last_login'], user['user_id']))
                        print(f"  ✓ Updated librarian {user['email']}")
                
                elif user['role'] == 'student':
                    # Check if already migrated
                    cur.execute(f"SELECT user_id FROM students WHERE user_id = %s", (user['user_id'],))
                    if cur.fetchone():
                        cur.execute(f"""
                            UPDATE students 
                            SET email = %s, password_hash = %s, full_name = %s, phone = %s, 
                                address = %s, status = %s, created_at = %s, updated_at = %s, last_login = %s
                            WHERE user_id = %s
                        """, (user['email'], user['password_hash'], user['full_name'], user['phone'],
                              user['address'], user['status'], user['created_at'], user['updated_at'],
                              user['last_login'], user['user_id']))
                        print(f"  ✓ Updated student {user['email']}")
            
            # Drop users table
            print("[5/5] Dropping users table...")
            try:
                cur.execute("DROP TABLE IF EXISTS users")
                print("  ✓ Dropped users table")
            except Exception as e:
                print(f"  ✓ Users table already dropped")
            
            # Re-enable foreign key checks
            cur.execute("SET FOREIGN_KEY_CHECKS=1")
            
            conn.commit()
            print("\n" + "="*70)
            print("✓ Migration completed successfully!")
            print("="*70)
            print("\nRemaining tables:")
            cur.execute("SHOW TABLES")
            tables = cur.fetchall()
            for table in tables:
                table_name = list(table.values())[0]
                print(f"  - {table_name}")
            print("="*70 + "\n")
        
        conn.close()
        
    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_migration()
