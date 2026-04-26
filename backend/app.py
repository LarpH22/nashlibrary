# -*- coding: utf-8 -*-
import os
import pymysql
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

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

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ─────────────────────────────
# Fallback HTML
# ─────────────────────────────
def create_fallback_html():
    return '''<!DOCTYPE html>
<html>
<head>
    <title>LIBRX - Building...</title>
    <style>
        body { font-family: Arial; text-align: center; padding: 50px; background: #0a0f1e; color: #fff; }
        h1 { color: #e51c1c; }
        p { color: #94a3b8; }
    </style>
</head>
<body>
    <h1>LIBRX</h1>
    <p>Frontend is building...</p>
    <p>Run: <code>cd frontend && npm install && npm run build</code></p>
</body>
</html>'''


# ─────────────────────────────
# DB Connection
# ─────────────────────────────
def get_connection():
    return pymysql.connect(
        host=Config.DB_HOST,
        port=int(Config.DB_PORT),
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        charset='utf8mb4'
    )


# ─────────────────────────────
# Safe schema check
# ─────────────────────────────
def column_exists(table, column):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) AS cnt
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s
            """, (Config.DB_NAME, table, column))
            return cur.fetchone()['cnt'] > 0


def ensure_schema():
    with get_connection() as conn:
        with conn.cursor() as cur:

            # Fix users status enum safely (no crash if fails)
            try:
                cur.execute("""
                    ALTER TABLE users 
                    MODIFY status ENUM('active','inactive','suspended','pending') DEFAULT 'active'
                """)
            except Exception:
                pass

            # Safe column add
            if not column_exists('students', 'proof_file'):
                try:
                    cur.execute("""
                        ALTER TABLE students 
                        ADD COLUMN proof_file VARCHAR(255) DEFAULT NULL
                    """)
                except Exception:
                    pass

        conn.commit()


# ─────────────────────────────
# Validation
# ─────────────────────────────
def validate_registration(full_name, email, password, phone, address):
    if not all([full_name, email, password, phone, address]):
        return 'All fields are required.'
    if len(full_name.strip()) < 3:
        return 'Full name too short.'
    if not EMAIL_REGEX.match(email):
        return 'Invalid email.'
    if len(password) < 6:
        return 'Password too short.'
    return None


def validate_login(username, password):
    if not username or not password:
        return 'Missing credentials.'
    return None


# ─────────────────────────────
# Init schema
# ─────────────────────────────
try:
    ensure_schema()
except Exception as e:
    print("Schema warning:", e)


# ─────────────────────────────
# Routes
# ─────────────────────────────

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or request.form

    full_name = data.get('full_name') or data.get('username')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')
    address = data.get('address')
    role = data.get('role', 'student')

    error = validate_registration(full_name, email, password, phone, address)
    if error:
        return jsonify({'message': error}), 400

    hashed = generate_password_hash(password)
    status = 'pending' if role == 'student' else 'active'

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("SELECT user_id FROM users WHERE email=%s", (email,))
            if cur.fetchone():
                return jsonify({'message': 'Email already exists'}), 400

            cur.execute("""
                INSERT INTO users (email, password_hash, full_name, phone, address, role, status)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (email, hashed, full_name, phone, address, role, status))

        conn.commit()

    return jsonify({'message': 'Registered successfully'}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    user_input = data.get('username')
    password = data.get('password')

    error = validate_login(user_input, password)
    if error:
        return jsonify({'message': error}), 400

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM users 
                WHERE email=%s OR full_name=%s
            """, (user_input, user_input))
            user = cur.fetchone()

            if not user or not check_password_hash(user['password_hash'], password):
                return jsonify({'message': 'Invalid login'}), 401

            token = create_access_token(identity=user['email'])

            return jsonify({
                'access_token': token,
                'role': user['role'],
                'message': 'Login successful'
            }), 200


@app.route('/user', methods=['GET'])
@jwt_required()
def get_user():
    email = get_jwt_identity()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cur.fetchone()

    return jsonify(user or {}), 200


# ─────────────────────────────
# Stats
# ─────────────────────────────
@app.route('/stats', methods=['GET'])
def get_stats():
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("SELECT COALESCE(SUM(total_copies),0) AS c FROM books")
            total_books = cur.fetchone()['c']

            cur.execute("SELECT COALESCE(SUM(available_copies),0) AS c FROM books")
            available_books = cur.fetchone()['c']

            cur.execute("SELECT COUNT(*) AS c FROM borrow_records WHERE status='borrowed'")
            borrowed_books = cur.fetchone()['c']

            cur.execute("SELECT COUNT(*) AS c FROM users WHERE role='student'")
            total_members = cur.fetchone()['c']

    return jsonify({
        "total_books": total_books,
        "available_books": available_books,
        "borrowed_books": borrowed_books,
        "total_members": total_members
    }), 200


def get_current_user_and_student():
    email = get_jwt_identity()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cur.fetchone()
            if not user:
                return None, None
            cur.execute("SELECT * FROM students WHERE user_id=%s", (user['user_id'],))
            student = cur.fetchone()
    return user, student


def get_default_librarian_id():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT librarian_id FROM librarians LIMIT 1")
            row = cur.fetchone()
            return row['librarian_id'] if row else None


@app.route('/books', methods=['GET'])
def list_books():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT book_id, isbn, title, author, publisher, publication_year, category, description, total_copies, available_copies, location, added_date FROM books ORDER BY book_id DESC")
            books = cur.fetchall()
    return jsonify(books), 200


@app.route('/borrowings', methods=['GET'])
@jwt_required()
def list_borrowings():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT br.borrow_id, br.student_id, br.book_id, br.borrow_date, br.due_date, br.return_date, br.status, br.notes, br.fine_amount, br.fine_paid, b.title AS book_title, b.category, u.email AS student_email "
                "FROM borrow_records br "
                "JOIN students s ON br.student_id=s.student_id "
                "JOIN users u ON s.user_id=u.user_id "
                "JOIN books b ON br.book_id=b.book_id "
                "ORDER BY br.borrow_date DESC"
            )
            borrowings = cur.fetchall()
    return jsonify(borrowings), 200


@app.route('/student/profile', methods=['GET', 'PUT'])
@jwt_required()
def student_profile():
    user, student = get_current_user_and_student()
    if not user or not student:
        return jsonify({'message': 'Student profile not found'}), 404

    if request.method == 'GET':
        profile = {
            'full_name': user.get('full_name'),
            'email': user.get('email'),
            'phone': user.get('phone'),
            'address': user.get('address'),
            'student_number': student.get('student_number'),
            'department': student.get('department'),
            'year_level': student.get('year_level'),
            'section': student.get('section'),
            'borrowed_books_count': student.get('borrowed_books_count'),
            'total_fines': float(student.get('total_fines') or 0),
            'library_card_number': student.get('library_card_number'),
            'expiration_date': student.get('expiration_date')
        }
        return jsonify(profile), 200

    data = request.get_json() or {}
    phone = data.get('phone')
    address = data.get('address')
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET phone=%s, address=%s WHERE user_id=%s", (phone, address, user['user_id']))
        conn.commit()
    return jsonify({'message': 'Profile updated.'}), 200


@app.route('/borrow', methods=['POST'])
@jwt_required()
def borrow_book():
    user, student = get_current_user_and_student()
    if not user or not student:
        return jsonify({'message': 'Student account not found'}), 404

    data = request.get_json() or {}
    book_id = data.get('book_id')
    due_date = data.get('due_date')
    if not book_id:
        return jsonify({'message': 'book_id is required'}), 400
    if not due_date:
        due_date = (datetime.utcnow() + timedelta(days=14)).date().isoformat()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT available_copies FROM books WHERE book_id=%s", (book_id,))
            book = cur.fetchone()
            if not book:
                return jsonify({'message': 'Book not found'}), 404
            if book['available_copies'] <= 0:
                return jsonify({'message': 'Book is not available'}), 400

            librarian_id = get_default_librarian_id() or 1
            borrow_date = datetime.utcnow().date().isoformat()

            cur.execute(
                "INSERT INTO borrow_records (student_id, book_id, librarian_id, borrow_date, due_date, status) VALUES (%s, %s, %s, %s, %s, 'borrowed')",
                (student['student_id'], book_id, librarian_id, borrow_date, due_date)
            )
            cur.execute("UPDATE books SET available_copies = available_copies - 1 WHERE book_id=%s", (book_id,))
            cur.execute("UPDATE students SET borrowed_books_count = borrowed_books_count + 1 WHERE student_id=%s", (student['student_id'],))
        conn.commit()

    return jsonify({'message': 'Book borrowed successfully.'}), 200


@app.route('/borrowings/<int:borrow_id>/return', methods=['POST'])
@jwt_required()
def return_book(borrow_id):
    user, student = get_current_user_and_student()
    if not user or not student:
        return jsonify({'message': 'Student account not found'}), 404

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM borrow_records WHERE borrow_id=%s AND student_id=%s", (borrow_id, student['student_id']))
            record = cur.fetchone()
            if not record:
                return jsonify({'message': 'Borrow record not found'}), 404
            if record['status'] == 'returned':
                return jsonify({'message': 'Book already returned'}), 400

            return_date = datetime.utcnow().date().isoformat()
            cur.execute(
                "UPDATE borrow_records SET status='returned', return_date=%s WHERE borrow_id=%s",
                (return_date, borrow_id)
            )
            cur.execute("UPDATE books SET available_copies = available_copies + 1 WHERE book_id=%s", (record['book_id'],))
            cur.execute("UPDATE students SET borrowed_books_count = GREATEST(borrowed_books_count - 1, 0) WHERE student_id=%s", (student['student_id'],))
        conn.commit()

    return jsonify({'message': 'Book returned successfully.'}), 200


@app.route('/student/fines', methods=['GET'])
@jwt_required()
def get_fines():
    user, student = get_current_user_and_student()
    if not user or not student:
        return jsonify({'message': 'Student account not found'}), 404

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT f.fine_id, f.amount, f.reason, f.status, f.issued_date, f.paid_date, b.title AS book_title, br.borrow_id "
                "FROM fines f "
                "LEFT JOIN borrow_records br ON f.borrow_id=br.borrow_id "
                "LEFT JOIN books b ON br.book_id=b.book_id "
                "WHERE f.student_id=%s "
                "ORDER BY f.issued_date DESC",
                (student['student_id'],)
            )
            fines = cur.fetchall()

            total_pending = sum(float(item['amount']) for item in fines if item['status'] == 'pending')
            total_paid = sum(float(item['amount']) for item in fines if item['status'] == 'paid')

    return jsonify({
        'total_pending': total_pending,
        'total_paid': total_paid,
        'fines': fines
    }), 200


@app.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, email, full_name, role, status FROM users ORDER BY user_id DESC")
            users = cur.fetchall()
    return jsonify(users), 200


# ─────────────────────────────
# Static Frontend
# ─────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIST = os.path.join(BASE_DIR, 'dist')


@app.route('/')
def index():
    path = os.path.join(FRONTEND_DIST, 'index.html')
    if os.path.exists(path):
        return send_from_directory(FRONTEND_DIST, 'index.html')
    return create_fallback_html()


@app.route('/<path:path>')
def static_files(path):
    file_path = os.path.join(FRONTEND_DIST, path)

    if os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIST, path)

    return index()


# ─────────────────────────────
# Run app
# ─────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')