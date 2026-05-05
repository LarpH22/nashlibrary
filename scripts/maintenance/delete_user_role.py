#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to delete all users with role='user' from the database
This keeps only admin, librarian, and student roles
"""

import pymysql
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Database configuration
DB_HOST = os.environ.get('DB_HOST') or '127.0.0.1'
DB_PORT = int(os.environ.get('DB_PORT', '3307'))
DB_USER = os.environ.get('DB_USER') or 'root'
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME') or 'library_system_v2'

def delete_user_role_accounts():
    """Delete all users with role='user'"""
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
            # First, check how many users with role='user' exist
            cur.execute("SELECT COUNT(*) as count FROM users WHERE role = 'user'")
            result = cur.fetchone()
            count = result['count'] if result else 0
            
            print(f"\nFound {count} users with role='user'")
            
            if count > 0:
                # Display users before deletion
                cur.execute("SELECT user_id, email, full_name, role FROM users WHERE role = 'user'")
                users = cur.fetchall()
                print("\nUsers to be deleted:")
                for user in users:
                    print(f"  - ID: {user['user_id']}, Email: {user['email']}, Name: {user['full_name']}")
                
                # Confirm before deletion
                confirm = input("\nAre you sure you want to delete these users? (yes/no): ").strip().lower()
                
                if confirm == 'yes':
                    # Temporarily disable foreign key checks
                    cur.execute("SET FOREIGN_KEY_CHECKS=0")
                    
                    # Get user IDs to delete
                    cur.execute("SELECT user_id FROM users WHERE role = 'user'")
                    user_ids = [row['user_id'] for row in cur.fetchall()]
                    
                    # Delete related records first
                    for uid in user_ids:
                        cur.execute("DELETE FROM audit_logs WHERE user_id = %s", (uid,))
                        cur.execute("DELETE FROM fines WHERE student_id IN (SELECT student_id FROM students WHERE user_id = %s)", (uid,))
                        cur.execute("DELETE FROM borrow_records WHERE student_id IN (SELECT student_id FROM students WHERE user_id = %s)", (uid,))
                        cur.execute("DELETE FROM students WHERE user_id = %s", (uid,))
                        cur.execute("DELETE FROM librarians WHERE user_id = %s", (uid,))
                        cur.execute("DELETE FROM admins WHERE user_id = %s", (uid,))
                    
                    # Delete users with role='user'
                    cur.execute("DELETE FROM users WHERE role = 'user'")
                    
                    # Re-enable foreign key checks
                    cur.execute("SET FOREIGN_KEY_CHECKS=1")
                    
                    conn.commit()
                    print(f"\n✓ Successfully deleted {count} users with role='user' and related records")
                else:
                    print("\nDeletion cancelled.")
            else:
                print("No users with role='user' found.")
        
        conn.close()
        
    except pymysql.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    delete_user_role_accounts()
