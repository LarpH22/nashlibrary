#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify remaining users in database
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

conn = pymysql.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    cursorclass=pymysql.cursors.DictCursor
)

with conn.cursor() as cur:
    cur.execute('SELECT user_id, email, full_name, role FROM users ORDER BY role')
    users = cur.fetchall()
    print('\n✓ Remaining users in database:')
    print('-' * 70)
    for user in users:
        print(f"  ID: {user['user_id']:2d} | Role: {user['role']:10s} | {user['email']:25s} | {user['full_name']}")
    print('-' * 70)
    
    cur.execute('SELECT DISTINCT role FROM users')
    roles = cur.fetchall()
    role_list = sorted([r['role'] for r in roles])
    print(f'\n✓ Roles remaining in system: {role_list}')
    print(f'✓ Total users: {len(users)}')

conn.close()
