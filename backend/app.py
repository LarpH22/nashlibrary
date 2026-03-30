# -*- coding: utf-8 -*-
import os
import subprocess
import pymysql
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

try:
    from backend.config import Config
except ModuleNotFoundError:
    from config import Config

import re

EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)
jwt = JWTManager(app)


def create_fallback_html():
    """Create fallback HTML when dist folder doesn't exist"""
    return '''<!DOCTYPE html>
<html>
<head>
    <title>NashLibrary - Building...</title>
    <style>
        body { font-family: Arial; text-align: center; padding: 50px; background: #0a0f1e; color: #fff; }
        h1 { color: #e51c1c; }
        p { color: #94a3b8; }
    </style>
</head>
<body>
    <h1>NashLibrary</h1>
    <p>Frontend is building...</p>
    <p>Run: <code>cd frontend && npm install && npm run build</code></p>
    <p>Then refresh this page.</p>
</body>
</html>'''


def get_connection():
    return pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        charset='utf8mb4'
    )


def validate_registration(full_name, email, password):
    if not full_name or not email or not password:
        return 'Full name, email, and password are required.'
    if len(full_name.strip()) < 3:
        return 'Full name must be at least 3 characters long.'
    if not EMAIL_REGEX.match(email):
        return 'Enter a valid email address.'
    if len(password) < 6:
        return 'Password must be at least 6 characters long.'
    if ' ' in password:
        return 'Password must not contain spaces.'
    return None


def validate_login(username, password):
    if not username or not password:
        return 'Username/email and password are required.'
    if len(username.strip()) < 3:
        return 'Please supply a valid username or email.'
    if len(password) < 6:
        return 'Password must be at least 6 characters long.'
    return None


# Test connection
try:
    conn = get_connection()
    conn.cursor().execute('SELECT 1')
    conn.close()
    print('MySQL connection successful')
except Exception as e:
    print(f'MySQL connection failed: {e}')
    exit(1)


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    full_name = data.get('username') or data.get('full_name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'student')

    error = validate_registration(full_name, email, password)
    if error:
        return jsonify({'message': error}), 400

    hashed = generate_password_hash(password)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT user_id FROM users WHERE full_name=%s OR email=%s', (full_name, email))
            existing = cur.fetchone()
            if existing:
                return jsonify({'message': 'User already exists with this name or email'}), 400

            cur.execute(
                'INSERT INTO users (full_name, email, password, role, created_at) VALUES (%s,%s,%s,%s,%s)',
                (full_name, email, hashed, role, datetime.utcnow())
            )
            user_id = cur.lastrowid

            if role == 'student':
                cur.execute('INSERT INTO students (user_id) VALUES (%s)', (user_id,))
            elif role == 'librarian':
                cur.execute('INSERT INTO librarians (user_id) VALUES (%s)', (user_id,))

        conn.commit()

    return jsonify({'message': 'User registered successfully'}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    user_input = data.get('username') or data.get('email')
    password = data.get('password')

    error = validate_login(user_input, password)
    if error:
        return jsonify({'message': error}), 400

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE full_name=%s OR email=%s', (user_input, user_input))
            user = cur.fetchone()
            if user and check_password_hash(user['password'], password):
                token = create_access_token(identity=user['email'])
                return jsonify({'access_token': token, 'role': user['role'], 'message': 'Logged in successfully'}), 200

    return jsonify({'message': 'Invalid username/email or password'}), 401


@app.route('/user', methods=['GET'])
@jwt_required()
def get_user():
    email = get_jwt_identity()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT full_name, email, role FROM users WHERE email=%s', (email,))
            user = cur.fetchone()
            if user:
                return jsonify(user), 200
    return jsonify({'message': 'User not found'}), 404


@app.route('/books', methods=['GET'])
@jwt_required()
def list_books():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT book_id, title, author, category, quantity, available FROM books')
            books = cur.fetchall()
    return jsonify(books), 200


@app.route('/books', methods=['POST'])
@jwt_required()
def add_book():
    email = get_jwt_identity()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT role FROM users WHERE email=%s', (email,))
            user = cur.fetchone()
            if not user or user['role'] not in ('librarian', 'admin'):
                return jsonify({'message': 'Permission denied'}), 403

            data = request.get_json() or {}
            title = data.get('title')
            author = data.get('author')
            category = data.get('category')
            quantity = int(data.get('quantity', 0))
            available = int(data.get('available', quantity))
            if not title or not author:
                return jsonify({'message': 'Title and author are required'}), 400

            cur.execute(
                'INSERT INTO books (title, author, category, quantity, available, created_at) VALUES (%s,%s,%s,%s,%s,%s)',
                (title, author, category, quantity, available, datetime.utcnow())
            )
            book_id = cur.lastrowid
            conn.commit()
            return jsonify({'message': 'Book added successfully', 'book_id': book_id}), 201


@app.route('/borrow', methods=['POST'])
@jwt_required()
def borrow_book():
    email = get_jwt_identity()
    data = request.get_json() or {}
    book_id = data.get('book_id')
    due_date = data.get('due_date')

    if not book_id or not due_date:
        return jsonify({'message': 'book_id and due_date are required'}), 400

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT user_id, role FROM users WHERE email=%s', (email,))
            user = cur.fetchone()
            if not user:
                return jsonify({'message': 'User not found'}), 404

            if user['role'] != 'student':
                return jsonify({'message': 'Only students can borrow books'}), 403

            cur.execute('SELECT student_id FROM students WHERE user_id=%s', (user['user_id'],))
            student = cur.fetchone()
            if not student:
                cur.execute('INSERT INTO students (user_id) VALUES (%s)', (user['user_id'],))
                student_id = cur.lastrowid
            else:
                student_id = student['student_id']

            cur.execute('SELECT available, quantity FROM books WHERE book_id=%s', (book_id,))
            book = cur.fetchone()
            if not book or book['available'] < 1:
                return jsonify({'message': 'Book is not available for borrowing'}), 400

            cur.execute('UPDATE books SET available=available-1 WHERE book_id=%s', (book_id,))
            cur.execute(
                'INSERT INTO borrow_records (student_id, book_id, borrow_date, return_date, status) VALUES (%s,%s,%s,%s,%s)',
                (student_id, book_id, datetime.utcnow(), None, 'borrowed')
            )
            borrow_id = cur.lastrowid
            conn.commit()
            return jsonify({'message': 'Book borrowed', 'borrow_record_id': borrow_id}), 201


@app.route('/return', methods=['POST'])
@jwt_required()
def return_book():
    data = request.get_json() or {}
    borrow_id = data.get('borrow_id')
    if not borrow_id:
        return jsonify({'message': 'borrow_id is required'}), 400

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT borrow_id, book_id, status FROM borrow_records WHERE borrow_id=%s', (borrow_id,))
            record = cur.fetchone()
            if not record:
                return jsonify({'message': 'Borrow record not found'}), 404
            if record['status'] == 'returned':
                return jsonify({'message': 'Book already returned'}), 400

            cur.execute('UPDATE borrow_records SET return_date=%s, status=%s WHERE borrow_id=%s', (datetime.utcnow(), 'returned', borrow_id))
            cur.execute('UPDATE books SET available=LEAST(quantity, available+1) WHERE book_id=%s', (record['book_id'],))
            conn.commit()
            return jsonify({'message': 'Book returned'}), 200


@app.route('/fines', methods=['GET'])
@jwt_required()
def list_fines():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT fine_id, borrow_id, amount, status FROM fines')
            fines = cur.fetchall()
    return jsonify(fines), 200


@app.route('/fines', methods=['POST'])
@jwt_required()
def add_fine():
    email = get_jwt_identity()
    data = request.get_json() or {}
    borrow_id = data.get('borrow_id')
    amount = data.get('amount')

    if not borrow_id or amount is None:
        return jsonify({'message': 'borrow_id and amount are required'}), 400

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT role FROM users WHERE email=%s', (email,))
            user = cur.fetchone()
            if not user or user['role'] not in ('librarian', 'admin'):
                return jsonify({'message': 'Permission denied'}), 403

            cur.execute('INSERT INTO fines (borrow_id, amount, status) VALUES (%s,%s,%s)', (borrow_id, amount, 'unpaid'))
            fine_id = cur.lastrowid
            conn.commit()
            return jsonify({'message': 'Fine created', 'fine_id': fine_id}), 201


@app.route('/stats', methods=['GET'])
def get_stats():
    """Get library statistics"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Total books
            cur.execute('SELECT COUNT(*) as count FROM books')
            total_books = cur.fetchone()['count'] or 0
            
            # Available books
            cur.execute('SELECT COALESCE(SUM(available), 0) as count FROM books')
            available_books = cur.fetchone()['count'] or 0
            
            # Borrowed books
            cur.execute("SELECT COUNT(*) as count FROM borrow_records WHERE status='borrowed'")
            borrowed_books = cur.fetchone()['count'] or 0
            
            # Total members (students)
            cur.execute("SELECT COUNT(*) as count FROM users WHERE role='student'")
            total_members = cur.fetchone()['count'] or 0
    
    return jsonify({
        'total_books': total_books,
        'available_books': available_books,
        'borrowed_books': borrowed_books,
        'total_members': total_members
    }), 200


# ── FRONTEND SERVING (routes at end so API routes match first) ──
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIST = os.path.join(BASE_DIR, 'dist')


@app.route('/', methods=['GET'])
def serve_index():
    """Serve the main frontend index.html for SPA routing"""
    index_path = os.path.join(FRONTEND_DIST, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(FRONTEND_DIST, 'index.html')
    return create_fallback_html()


@app.route('/<path:path>', methods=['GET'])
def serve_static(path):
    """Serve static files (JS, CSS, images, etc.) or fallback for SPA routing"""
    if path.startswith('api/'):
        return jsonify({'message': 'API not found'}), 404
    
    file_path = os.path.join(FRONTEND_DIST, path)
    if os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIST, path)
    
    index_path = os.path.join(FRONTEND_DIST, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(FRONTEND_DIST, 'index.html')
    return create_fallback_html()


if __name__ == '__main__':
    app.run(debug=True)
