# -*- coding: utf-8 -*-
import os
import subprocess
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
        port=int(Config.DB_PORT),
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        charset='utf8mb4'
    )

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def ensure_schema():
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("ALTER TABLE users MODIFY COLUMN status ENUM('active','inactive','suspended','pending') DEFAULT 'active';")
            except Exception:
                pass
            try:
                cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS proof_file VARCHAR(255) DEFAULT NULL;")
            except Exception:
                pass
        conn.commit()


def validate_registration(full_name, email, password, phone, address):
    if not full_name or not email or not password or not phone or not address:
        return 'Full name, email, phone number, address, and password are required.'
    if len(full_name.strip()) < 3:
        return 'Full name must be at least 3 characters long.'
    if not EMAIL_REGEX.match(email):
        return 'Enter a valid email address.'
    if len(password) < 6:
        return 'Password must be at least 6 characters long.'
    if ' ' in password:
        return 'Password must not contain spaces.'
    if len(phone.strip()) < 7:
        return 'Enter a valid phone number.'
    if len(address.strip()) < 5:
        return 'Enter a valid address.'
    return None


def validate_login(username, password):
    if not username or not password:
        return 'Username/email and password are required.'
    if len(username.strip()) < 3:
        return 'Please supply a valid username or email.'
    if len(password) < 6:
        return 'Password must be at least 6 characters long.'
    return None


# Ensure DB schema supports pending registrations and uploads
try:
    ensure_schema()
except Exception as e:
    print(f'Warning: schema ensure failed: {e}')

if Config.DB_USER == 'root' and Config.DB_PASSWORD is None:
    print('Error: DB_PASSWORD is not set for MySQL root user.')
    print('Create a .env file in the repository root or set DB_PASSWORD in your environment.')
    print('Hint: copy .env.example to .env and update DB_PASSWORD before restarting.')
    exit(1)

if Config.DB_USER == 'root' and Config.DB_PASSWORD == '':
    print('Warning: DB_PASSWORD is blank for MySQL root user. This is insecure but allowed if your MySQL root account has no password.')

# Test connection
try:
    conn = get_connection()
    conn.cursor().execute('SELECT 1')
    conn.close()
    print('MySQL connection successful')
except Exception as e:
    print(f'MySQL connection failed: {e}')
    print('Check DB_HOST, DB_PORT, DB_USER, and DB_PASSWORD settings in your environment or .env file.')
    exit(1)


@app.route('/register', methods=['POST'])
def register():
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form
        proof_file = request.files.get('proof')
    else:
        data = request.get_json() or {}
        proof_file = None

    full_name = data.get('full_name') or data.get('username')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')
    address = data.get('address')
    role = data.get('role', 'student').lower()

    if role not in ('student', 'user', 'librarian', 'admin'):
        return jsonify({'message': 'Invalid role selected.'}), 400

    error = validate_registration(full_name, email, password, phone, address)
    if error:
        return jsonify({'message': error}), 400

    if role == 'student' and not proof_file:
        return jsonify({'message': 'Proof of enrollment is required for student registration.'}), 400

    if role != 'student' and proof_file:
        return jsonify({'message': 'Enrollment proof is only required for student registration.'}), 400

    hashed = generate_password_hash(password)
    status = 'pending' if role == 'student' else 'active'
    proof_filename = None

    if role == 'student' and proof_file and proof_file.filename:
        filename = secure_filename(proof_file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        proof_filename = f'{timestamp}_{filename}'
        proof_path = os.path.join(UPLOAD_FOLDER, proof_filename)
        proof_file.save(proof_path)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT user_id FROM users WHERE email=%s', (email,))
            existing = cur.fetchone()
            if existing:
                return jsonify({'message': 'A user already exists with this email address.'}), 400

            cur.execute(
                'INSERT INTO users (email, password_hash, full_name, phone, address, role, status) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                (email, hashed, full_name, phone, address, role, status)
            )
            user_id = cur.lastrowid

            if role == 'student':
                cur.execute(
                    'INSERT INTO students (user_id, student_number, proof_file) VALUES (%s,%s,%s)',
                    (user_id, f'STU{user_id:05d}', proof_filename)
                )
            elif role == 'librarian':
                cur.execute('INSERT INTO librarians (user_id, employee_id) VALUES (%s,%s)', (user_id, f'LIB{user_id:05d}'))
            elif role == 'admin':
                cur.execute('INSERT INTO admins (user_id, admin_level) VALUES (%s,%s)', (user_id, 'junior'))

        conn.commit()

    if role == 'student':
        return jsonify({'message': 'Registration submitted. Student accounts require admin approval.'}), 201

    return jsonify({'message': 'Registration successful. Your account is now active.'}), 201


@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        user_input = data.get('username') or data.get('email')
        password = data.get('password')

        error = validate_login(user_input, password)
        if error:
            return jsonify({'message': error}), 400

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT user_id, email, password_hash, role, full_name, status FROM users WHERE full_name=%s OR email=%s', (user_input, user_input))
                user = cur.fetchone()
                if user and check_password_hash(user['password_hash'], password):
                    if user['status'] == 'pending':
                        return jsonify({'message': 'Your account is pending admin approval.'}), 403
                    if user['status'] == 'inactive':
                        return jsonify({'message': 'Your account is inactive. Contact admin.'}), 403
                    if user['status'] == 'suspended':
                        return jsonify({'message': 'Your account is suspended.'}), 403

                    token = create_access_token(identity=user['email'])
                    return jsonify({'access_token': token, 'role': user['role'], 'message': 'Logged in successfully'}), 200

        return jsonify({'message': 'Invalid username/email or password'}), 401
    except Exception as e:
        print(f'Login error: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Server error: {str(e)}'}), 500


@app.route('/user', methods=['GET'])
@jwt_required()
def get_user():
    email = get_jwt_identity()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT user_id, email, full_name, phone, address, role, status FROM users WHERE email=%s', (email,))
            user = cur.fetchone()
            if user:
                return jsonify({
                    'user_id': user['user_id'],
                    'email': user['email'],
                    'username': user['full_name'],
                    'full_name': user['full_name'],
                    'phone': user['phone'],
                    'address': user.get('address'),
                    'role': user['role'],
                    'status': user['status']
                }), 200
    return jsonify({'message': 'User not found'}), 404


@app.route('/student/profile', methods=['GET'])
@jwt_required()
def get_student_profile():
    email = get_jwt_identity()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT u.user_id, u.email, u.full_name, u.phone, u.address, u.status, '
                's.student_number, s.department, s.year_level, s.section, s.borrowed_books_count, '
                's.total_fines, s.library_card_number, s.expiration_date '
                'FROM users u '
                'LEFT JOIN students s ON u.user_id = s.user_id '
                'WHERE u.email = %s',
                (email,)
            )
            student = cur.fetchone()
            if not student:
                return jsonify({'message': 'Student profile not found'}), 404
            return jsonify({
                'user_id': student['user_id'],
                'email': student['email'],
                'full_name': student['full_name'],
                'phone': student['phone'],
                'address': student['address'],
                'status': student['status'],
                'student_number': student['student_number'],
                'department': student['department'],
                'year_level': student['year_level'],
                'section': student['section'],
                'borrowed_books_count': student['borrowed_books_count'],
                'total_fines': float(student['total_fines'] or 0),
                'library_card_number': student['library_card_number'],
                'expiration_date': student['expiration_date'].isoformat() if student['expiration_date'] else None
            }), 200


@app.route('/student/profile', methods=['PUT'])
@jwt_required()
def update_student_profile():
    email = get_jwt_identity()
    data = request.get_json() or {}
    new_phone = data.get('phone')
    new_address = data.get('address')

    if new_phone is None and new_address is None:
        return jsonify({'message': 'No update fields provided'}), 400

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT user_id FROM users WHERE email=%s', (email,))
            user = cur.fetchone()
            if not user:
                return jsonify({'message': 'User not found'}), 404

            if new_phone is not None:
                cur.execute('UPDATE users SET phone=%s WHERE user_id=%s', (new_phone, user['user_id']))
            if new_address is not None:
                cur.execute('UPDATE users SET address=%s WHERE user_id=%s', (new_address, user['user_id']))
        conn.commit()

    return jsonify({'message': 'Profile updated successfully'}), 200


@app.route('/student/fines', methods=['GET'])
@jwt_required()
def get_student_fines():
    """Get current student's fines with details"""
    email = get_jwt_identity()
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Get user and student info
            cur.execute('SELECT user_id FROM users WHERE email=%s', (email,))
            user = cur.fetchone()
            if not user:
                return jsonify({'message': 'User not found'}), 404

            cur.execute('SELECT student_id FROM students WHERE user_id=%s', (user['user_id'],))
            student = cur.fetchone()
            if not student:
                return jsonify({'message': 'Student not found'}), 404

            # Get all fines for this student with book details
            cur.execute('''
                SELECT 
                    f.fine_id,
                    f.amount,
                    f.status,
                    f.reason,
                    f.issued_date,
                    f.paid_date,
                    b.title AS book_title,
                    br.due_date,
                    br.return_date,
                    DATEDIFF(NOW(), f.issued_date) as days_overdue
                FROM fines f
                LEFT JOIN borrow_records br ON f.borrow_id = br.borrow_id
                LEFT JOIN books b ON br.book_id = b.book_id
                WHERE f.student_id=%s
                ORDER BY f.issued_date DESC
            ''', (student['student_id'],))
            
            fines = cur.fetchall()
            
            # Calculate summary
            total_pending = 0
            total_paid = 0
            for fine in fines:
                if fine['status'] == 'pending':
                    total_pending += fine['amount']
                elif fine['status'] == 'paid':
                    total_paid += fine['amount']
            
            return jsonify({
                'fines': fines,
                'total_pending': float(total_pending),
                'total_paid': float(total_paid),
                'total_fines': float(total_pending + total_paid)
            }), 200


@app.route('/books', methods=['GET'])
@jwt_required()
def list_books():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT book_id, title, author, category, total_copies, available_copies, location FROM books')
            books = cur.fetchall()
    return jsonify(books), 200


@app.route('/books', methods=['POST'])
@jwt_required()
def add_book():
    email = get_jwt_identity()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT user_id, role FROM users WHERE email=%s', (email,))
            user = cur.fetchone()
            if not user or user['role'] not in ('librarian', 'admin'):
                return jsonify({'message': 'Permission denied'}), 403

            data = request.get_json() or {}
            title = data.get('title')
            author = data.get('author')
            category = data.get('category')
            total_copies = int(data.get('total_copies', 1))
            location = data.get('location', 'Unknown')
            description = data.get('description', '')
            publisher = data.get('publisher', '')
            publication_year = data.get('publication_year')
            isbn = data.get('isbn', None)
            if not title or not author:
                return jsonify({'message': 'Title and author are required'}), 400

            cur.execute(
                'INSERT INTO books (isbn, title, author, publisher, publication_year, category, description, total_copies, available_copies, location, added_by, added_date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (isbn, title, author, publisher, publication_year, category, description, total_copies, total_copies, location, user['user_id'], datetime.utcnow())
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

            cur.execute('SELECT student_id, borrowed_books_count FROM students WHERE user_id=%s', (user['user_id'],))
            student = cur.fetchone()
            if not student:
                return jsonify({'message': 'Student profile not found'}), 404

            cur.execute('SELECT available_copies FROM books WHERE book_id=%s', (book_id,))
            book = cur.fetchone()
            if not book or book['available_copies'] < 1:
                return jsonify({'message': 'Book is not available for borrowing'}), 400

            cur.execute('UPDATE books SET available_copies=available_copies-1 WHERE book_id=%s', (book_id,))
            cur.execute('UPDATE students SET borrowed_books_count=borrowed_books_count+1 WHERE student_id=%s', (student['student_id'],))
            cur.execute(
                'INSERT INTO borrow_records (student_id, book_id, librarian_id, borrow_date, due_date, status) VALUES (%s,%s,%s,%s,%s,%s)',
                (student['student_id'], book_id, None, datetime.utcnow().date(), due_date, 'borrowed')
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
            cur.execute('SELECT borrow_id, book_id, student_id, status FROM borrow_records WHERE borrow_id=%s', (borrow_id,))
            record = cur.fetchone()
            if not record:
                return jsonify({'message': 'Borrow record not found'}), 404
            if record['status'] == 'returned':
                return jsonify({'message': 'Book already returned'}), 400

            cur.execute('UPDATE borrow_records SET return_date=%s, status=%s WHERE borrow_id=%s', (datetime.utcnow().date(), 'returned', borrow_id))
            cur.execute('UPDATE books SET available_copies=LEAST(total_copies, available_copies+1) WHERE book_id=%s', (record['book_id'],))
            cur.execute('UPDATE students SET borrowed_books_count=GREATEST(0, borrowed_books_count-1) WHERE student_id=%s', (record['student_id'],))
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
            cur.execute('SELECT user_id, role FROM users WHERE email=%s', (email,))
            user = cur.fetchone()
            if not user or user['role'] not in ('librarian', 'admin'):
                return jsonify({'message': 'Permission denied'}), 403

            # check borrow record exists and get student_id
            cur.execute('SELECT student_id FROM borrow_records WHERE borrow_id=%s', (borrow_id,))
            borrow_record = cur.fetchone()
            if not borrow_record:
                return jsonify({'message': 'Borrow record not found'}), 404

            student_id = borrow_record['student_id']
            cur.execute('INSERT INTO fines (borrow_id, student_id, amount, reason, status, issued_date, issued_by) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                        (borrow_id, student_id, amount, data.get('reason', 'Overdue fine'), 'pending', datetime.utcnow().date(), user['user_id']))
            fine_id = cur.lastrowid
            conn.commit()
            return jsonify({'message': 'Fine created', 'fine_id': fine_id}), 201


@app.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT u.user_id, u.email, u.full_name, u.role, u.status, s.student_number, s.proof_file '
                'FROM users u '
                'LEFT JOIN students s ON u.user_id = s.user_id'
            )
            users = cur.fetchall()
    return jsonify(users), 200


@app.route('/borrowings', methods=['GET'])
@jwt_required()
def list_borrowings():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT br.borrow_id, u.email AS student_email, b.title AS book_title, b.category AS category, br.borrow_date, br.due_date, br.return_date, br.status '
                'FROM borrow_records br '
                'LEFT JOIN students s ON br.student_id = s.student_id '
                'LEFT JOIN users u ON s.user_id = u.user_id '
                'LEFT JOIN books b ON br.book_id = b.book_id'
            )
            borrowings = cur.fetchall()
    return jsonify(borrowings), 200


@app.route('/stats', methods=['GET'])
def get_stats():
    """Get library statistics"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Total books
            cur.execute('SELECT COALESCE(SUM(total_copies), 0) as count FROM books')
            total_books = cur.fetchone()['count'] or 0
            
            # Available books
            cur.execute('SELECT COALESCE(SUM(available_copies), 0) as count FROM books')
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


@app.route('/uploads/<path:filename>', methods=['GET'])
@jwt_required()
def download_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@app.route('/users/<int:user_id>/status', methods=['PUT'])
@jwt_required()
def update_user_status(user_id):
    email = get_jwt_identity()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT role FROM users WHERE email=%s', (email,))
            user = cur.fetchone()
            if not user or user['role'] != 'admin':
                return jsonify({'message': 'Permission denied'}), 403

            data = request.get_json() or {}
            new_status = data.get('status')
            if not new_status:
                return jsonify({'message': 'Status is required'}), 400

            cur.execute('UPDATE users SET status=%s WHERE user_id=%s', (new_status, user_id))
        conn.commit()
    return jsonify({'message': 'User status updated'}), 200


@app.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    email = get_jwt_identity()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT role FROM users WHERE email=%s', (email,))
            user = cur.fetchone()
            if not user or user['role'] != 'admin':
                return jsonify({'message': 'Permission denied'}), 403

            cur.execute('DELETE FROM users WHERE user_id=%s', (user_id,))
        conn.commit()
    return jsonify({'message': 'User deleted'}), 200


@app.route('/books/<int:book_id>', methods=['DELETE'])
@jwt_required()
def delete_book(book_id):
    email = get_jwt_identity()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT role FROM users WHERE email=%s', (email,))
            user = cur.fetchone()
            if not user or user['role'] not in ('admin', 'librarian'):
                return jsonify({'message': 'Permission denied'}), 403

            cur.execute('DELETE FROM books WHERE book_id=%s', (book_id,))
        conn.commit()
    return jsonify({'message': 'Book deleted'}), 200


@app.route('/borrowings/<int:borrow_id>/return', methods=['POST'])
@jwt_required()
def process_book_return(borrow_id):
    email = get_jwt_identity()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT br.student_id, br.book_id FROM borrow_records br WHERE br.borrow_id=%s',
                (borrow_id,)
            )
            record = cur.fetchone()
            if not record:
                return jsonify({'message': 'Borrowing record not found'}), 404

            cur.execute('UPDATE borrow_records SET status=%s, return_date=%s WHERE borrow_id=%s',
                       ('returned', datetime.now().date(), borrow_id))
            cur.execute('UPDATE books SET available_copies=available_copies+1 WHERE book_id=%s', (record['book_id'],))
            cur.execute('UPDATE students SET borrowed_books_count=GREATEST(0, borrowed_books_count-1) WHERE student_id=%s', (record['student_id'],))
        conn.commit()
    return jsonify({'message': 'Book return processed'}), 200


@app.route('/fines/<int:fine_id>/pay', methods=['POST'])
@jwt_required()
def mark_fine_paid(fine_id):
    email = get_jwt_identity()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT role FROM users WHERE email=%s', (email,))
            user = cur.fetchone()
            if not user or user['role'] != 'admin':
                return jsonify({'message': 'Permission denied'}), 403

            cur.execute('UPDATE fines SET status=%s WHERE fine_id=%s', ('paid', fine_id))
        conn.commit()
    return jsonify({'message': 'Fine marked as paid'}), 200


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
