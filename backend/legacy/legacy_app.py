# -*- coding: utf-8 -*-
import os
import pymysql
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory, url_for
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_mail import Mail, Message
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import bcrypt
import re
import secrets
import hashlib
import threading

try:
    from backend.config import Config
except ModuleNotFoundError:
    from config import Config

EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")

app = Flask(__name__)
app.config.from_object(Config)
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
app.config['DEBUG'] = False
app.config['PROPAGATE_EXCEPTIONS'] = True

CORS(app)
jwt = JWTManager(app)
mail = Mail(app)

UPLOAD_FOLDER = Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS
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
    try:
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
    except pymysql.err.OperationalError as e:
        app.logger.error(
            f"Database connection failed: host={Config.DB_HOST}, port={Config.DB_PORT}, user={Config.DB_USER}. Error: {e}"
        )
        raise


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


def get_table_primary_key(table, candidate_columns):
    for column in candidate_columns:
        if column_exists(table, column):
            return column
    return None


def get_books_id_column():
    return get_table_primary_key('books', ['book_id', 'id']) or 'book_id'


def get_book_inventory_select_columns():
    has_available_copies = column_exists('books', 'available_copies')
    has_total_copies = column_exists('books', 'total_copies')

    if has_available_copies:
        total_expr = 'total_copies' if has_total_copies else 'NULL AS total_copies'
        return (
            "COALESCE(status, CASE WHEN available_copies > 0 THEN 'available' ELSE 'borrowed' END) AS status, "
            "available_copies, " + total_expr
        )

    return (
        "COALESCE(status, 'available') AS status, "
        "CASE WHEN status='borrowed' THEN 0 ELSE 1 END AS available_copies, "
        "1 AS total_copies"
    )


def table_exists(table):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) AS cnt
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s
            """, (Config.DB_NAME, table))
            return cur.fetchone()['cnt'] > 0


def delete_by_key(cur, table, column, user_id):
    try:
        cur.execute(f"DELETE FROM {table} WHERE {column}=%s", (user_id,))
        return cur.rowcount > 0
    except Exception:
        return False


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

            # Add status column if not exists
            if not column_exists('students', 'status'):
                try:
                    cur.execute("""
                        ALTER TABLE students 
                        ADD COLUMN status ENUM('pending', 'active', 'inactive', 'suspended', 'rejected') DEFAULT 'pending'
                    """)
                except Exception:
                    pass

            # Add email verification columns
            if not column_exists('students', 'email_verified'):
                try:
                    cur.execute("""
                        ALTER TABLE students 
                        ADD COLUMN email_verified BOOLEAN DEFAULT FALSE,
                        ADD COLUMN verification_token VARCHAR(255)
                    """)
                except Exception:
                    pass

            # Add reset password columns
            if not column_exists('students', 'reset_token'):
                try:
                    cur.execute("""
                        ALTER TABLE students
                        ADD COLUMN reset_token VARCHAR(255),
                        ADD COLUMN reset_expires_at TIMESTAMP NULL
                    """)
                except Exception:
                    pass

            # Add status column to librarians table if missing
            if not column_exists('librarians', 'status'):
                try:
                    cur.execute("""
                        ALTER TABLE librarians
                        ADD COLUMN status ENUM('active', 'inactive', 'suspended', 'pending', 'rejected') DEFAULT 'active'
                    """)
                except Exception:
                    pass

            # Create registration_requests table if missing
            try:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS registration_requests (
                        request_id INT PRIMARY KEY AUTO_INCREMENT,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        full_name VARCHAR(255) NOT NULL,
                        student_number VARCHAR(20) DEFAULT NULL,
                        registration_document VARCHAR(255) DEFAULT NULL,
                        verification_token VARCHAR(255) DEFAULT NULL,
                        email_verified BOOLEAN DEFAULT FALSE,
                        verified_at TIMESTAMP NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_email (email),
                        INDEX idx_verification_token (verification_token)
                    )
                """)
            except Exception:
                pass

            # Safe renewal metadata add for borrow records
            if not column_exists('borrow_records', 'renewal_count'):
                try:
                    cur.execute("""
                        ALTER TABLE borrow_records
                        ADD COLUMN renewal_count INT DEFAULT 0,
                        ADD COLUMN last_renewal_date DATE DEFAULT NULL
                    """)
                except Exception:
                    pass

        conn.commit()


# ─────────────────────────────
# Validation
# ─────────────────────────────
def validate_registration(full_name, email, password, student_id=None):
    # Ensure all are strings before processing
    full_name = full_name.strip() if isinstance(full_name, str) else ''
    email = email.strip() if isinstance(email, str) else ''
    password = password.strip() if isinstance(password, str) else ''
    student_id = student_id.strip() if isinstance(student_id, str) else None
    
    # Check all required fields are present
    missing_fields = []
    if not full_name:
        missing_fields.append('full name')
    if not email:
        missing_fields.append('email')
    if not password:
        missing_fields.append('password')
    if missing_fields:
        return f'The following fields are required: {", ".join(missing_fields)}.'
    if len(full_name) < 3 or len(full_name) > 100:
        return 'Full name must be between 3 and 100 characters.'
    if not EMAIL_REGEX.match(email):
        return 'Invalid email format.'
    # Check if email domain is @gmail.com or .edu.ph
    if not (email.endswith('@gmail.com') or email.endswith('.edu.ph')):
        return 'Email must end with @gmail.com or .edu.ph'
    if not PASSWORD_REGEX.match(password):
        return 'Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one number, and one special character.'
    if student_id and (len(student_id) < 3 or len(student_id) > 20):
        return 'Student ID must be between 3 and 20 characters.'
    return None

def validate_file(file, required=False):
    """
    Validate file upload.
    
    Args:
        file: The file object from request.files
        required: If True, file must be present. If False, file is optional.
    
    Returns:
        Error message string or None if valid
    """
    # Check if file is required but missing
    if required and (not file or file.filename == ''):
        return 'School Registration Document is required.'
    
    # If file is optional and not provided, validation passes
    if not required and (not file or file.filename == ''):
        return None
    
    # File exists, validate file type
    if not allowed_file(file.filename):
        return 'Invalid file type. Only PDF, JPG, JPEG, and PNG files are allowed.'

    # Validate file size
    try:
        file.stream.seek(0, os.SEEK_END)
        size = file.stream.tell()
        file.stream.seek(0)
    except Exception as e:
        app.logger.error(f'Error checking file size: {str(e)}')
        return 'Unable to read file size. Please try again.'

    if size is not None and size > 5 * 1024 * 1024:
        return 'File size must be less than 5MB.'
    
    if size == 0:
        return 'File is empty. Please upload a valid document.'
    
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_verification_token():
    return secrets.token_urlsafe(32)

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(hashed, password):
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except (ValueError, TypeError):
        pass

    try:
        if check_password_hash(hashed, password):
            return True
    except Exception:
        pass

    return hashed == password


def is_email_in_use(email):
    if not email:
        return False
    email = email.strip().lower()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM admins WHERE email=%s", (email,))
            if cur.fetchone():
                return True
            cur.execute("SELECT 1 FROM librarians WHERE email=%s", (email,))
            if cur.fetchone():
                return True
            cur.execute("SELECT 1 FROM students WHERE email=%s", (email,))
            if cur.fetchone():
                return True
            if column_exists('registration_requests', 'email'):
                cur.execute("SELECT 1 FROM registration_requests WHERE email=%s", (email,))
                if cur.fetchone():
                    return True
    return False


def get_registration_conflict_message(email):
    if not email:
        return None
    email = email.strip().lower()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT status, email_verified FROM students WHERE email=%s LIMIT 1", (email,))
            student = cur.fetchone()
            if student:
                if student.get('status') == 'active':
                    return 'This email already exists.'
                if student.get('status') == 'pending':
                    return 'This email already exists and is pending approval.'
                return 'This email already exists.'

            if column_exists('registration_requests', 'email'):
                cur.execute("SELECT email_verified FROM registration_requests WHERE email=%s LIMIT 1", (email,))
                request_row = cur.fetchone()
                if request_row:
                    if not request_row.get('email_verified'):
                        return 'This form already exists. Please check your email to verify your account.'
                    return 'This form already exists and is awaiting approval.'

            cur.execute("SELECT 1 FROM admins WHERE email=%s LIMIT 1", (email,))
            if cur.fetchone():
                return 'This email already exists.'
            cur.execute("SELECT 1 FROM librarians WHERE email=%s LIMIT 1", (email,))
            if cur.fetchone():
                return 'This email already exists.'
    return None


def validate_login(username, password):
    if not username or not password:
        return 'Missing credentials.'
    return None


def is_admin_user(email):
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Check if user is admin
            cur.execute("SELECT 1 FROM admins WHERE email=%s", (email,))
            if cur.fetchone():
                return True

            # Check if user is librarian (librarians also have admin privileges)
            cur.execute("SELECT 1 FROM librarians WHERE email=%s", (email,))
            return bool(cur.fetchone())


def find_account_by_identifier(identifier):
    identifier = identifier.strip() if isinstance(identifier, str) else identifier
    with get_connection() as conn:
        with conn.cursor() as cur:
            # First check the unified users table
            cur.execute(
                "SELECT user_id AS account_id, email, password_hash, full_name, role, status FROM users WHERE email=%s LIMIT 1",
                (identifier,)
            )
            account = cur.fetchone()
            if account:
                # For students, we need additional fields like email_verified
                if account.get('role') == 'student':
                    cur.execute(
                        "SELECT email_verified FROM students WHERE email=%s LIMIT 1",
                        (identifier,)
                    )
                    student_info = cur.fetchone()
                    if student_info:
                        account['email_verified'] = student_info['email_verified']
                    else:
                        account['email_verified'] = False
                else:
                    account['email_verified'] = True  # Non-students are assumed verified
                return account

            # Fallback to role-specific tables for backward compatibility
            cur.execute(
                "SELECT id AS account_id, email, password AS password_hash, fullname AS full_name, 'admin' AS role, status FROM admins WHERE email=%s LIMIT 1",
                (identifier,)
            )
            account = cur.fetchone()
            if account:
                account['email_verified'] = True
                return account

            cur.execute(
                "SELECT id AS account_id, email, password AS password_hash, fullname AS full_name, 'librarian' AS role, status FROM librarians WHERE email=%s LIMIT 1",
                (identifier,)
            )
            account = cur.fetchone()
            if account:
                account['email_verified'] = True
                return account

            cur.execute(
                "SELECT student_id AS account_id, email, password_hash, full_name, student_number, 'student' AS role, status, email_verified FROM students WHERE email=%s OR student_number=%s LIMIT 1",
                (identifier, identifier)
            )
            account = cur.fetchone()
            if account:
                account['email_verified'] = account.get('email_verified', False)
            return account


def find_account_by_email(email):
    email = email.strip() if isinstance(email, str) else email
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id AS account_id, email, fullname AS full_name, 'admin' AS role, 'active' AS status FROM admins WHERE email=%s LIMIT 1",
                (email,)
            )
            account = cur.fetchone()
            if account:
                return account

            cur.execute(
                "SELECT id AS account_id, email, fullname AS full_name, 'librarian' AS role, 'active' AS status FROM librarians WHERE email=%s LIMIT 1",
                (email,)
            )
            account = cur.fetchone()
            if account:
                return account

            cur.execute(
                "SELECT student_id AS account_id, email, full_name, student_number, 'student' AS role, status, email_verified FROM students WHERE email=%s LIMIT 1",
                (email,)
            )
            return cur.fetchone()


# ─────────────────────────────
# Init schema
# ─────────────────────────────
try:
    ensure_schema()
except Exception as e:
    print("Schema warning:", e)


# ─────────────────────────────
# Email utilities
# ─────────────────────────────
def send_email_async(subject, recipients, body, html_body=None):
    """Send email asynchronously in a background thread"""
    def _send():
        try:
            with app.app_context():
                msg = Message(subject, sender=Config.MAIL_DEFAULT_SENDER, recipients=recipients)
                msg.body = body
                if html_body:
                    msg.html = html_body
                mail.send(msg)
                app.logger.info(f'Email sent to {recipients}')
        except Exception as e:
            app.logger.error(f'Failed to send email to {recipients}: {str(e)}', exc_info=True)
    
    thread = threading.Thread(target=_send, daemon=True)
    thread.start()


# ─────────────────────────────
# Error Handlers
# ─────────────────────────────
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'message': 'Internal server error', 'error': str(error)}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    app.logger.error(f'Unhandled exception: {str(e)}\n{traceback.format_exc()}')
    return jsonify({'message': 'Internal server error', 'error': str(e)}), 500


# ─────────────────────────────
# Routes
# ─────────────────────────────

@app.route('/register', methods=['POST'])
def register():
    """
    Register a new user with improved error handling and async email sending.
    Safely handles None values and prevents 500 errors.
    Requires: full_name, email, password, registration_document (file upload)
    Optional: student_id
    """
    try:
        # Extract form data with safe defaults
        full_name = None
        email = None
        password = None
        student_id = None
        doc = None
        
        app.logger.info(f'Register request - Content-Type: {request.content_type}')
        
        # Try to extract from multipart form data
        if request.content_type and 'multipart/form-data' in request.content_type:
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()
            student_id = request.form.get('student_id', '').strip()
            doc = request.files.get('registration_document')
            
            app.logger.info(f'Extracted from FormData - full_name: {bool(full_name)}, email: {bool(email)}, password: {bool(password)}, student_id: {bool(student_id)}, doc: {bool(doc)}')
        else:
            # Try JSON first
            try:
                data = request.get_json(force=False, silent=True)
                if data and isinstance(data, dict):
                    full_name = data.get('full_name', '').strip() if isinstance(data.get('full_name'), str) else ''
                    email = data.get('email', '').strip() if isinstance(data.get('email'), str) else ''
                    password = data.get('password', '').strip() if isinstance(data.get('password'), str) else ''
                    student_id = data.get('student_id', '').strip() if isinstance(data.get('student_id'), str) else ''
                    app.logger.info(f'Extracted from JSON - full_name: {bool(full_name)}, email: {bool(email)}, password: {bool(password)}')
            except Exception as e:
                app.logger.debug(f'JSON parsing failed: {str(e)}')
            
            # Fall back to form data if needed
            if not email or not full_name or not password:
                full_name = request.form.get('full_name', '').strip()
                email = request.form.get('email', '').strip()
                password = request.form.get('password', '').strip()
                student_id = request.form.get('student_id', '').strip()
                app.logger.info(f'Fell back to form data extraction')
            
            doc = request.files.get('registration_document')

        # Normalize and validate input - convert empty strings to None
        email = email.lower() if email else None
        student_id = student_id if student_id else None

        # Remove simple HTML characters to reduce XSS risk
        if full_name:
            full_name = re.sub(r'[<>"\']', '', full_name)
        if student_id:
            student_id = re.sub(r'[<>"\']', '', student_id)

        # Validate registration data (basic fields)
        error = validate_registration(full_name, email, password, student_id)
        if error:
            app.logger.warning(f'Registration validation failed: {error}')
            return jsonify({'message': error}), 400

        # Validate file upload - REQUIRED
        file_error = validate_file(doc, required=True)
        if file_error:
            app.logger.warning(f'File validation failed: {file_error}')
            return jsonify({'message': file_error}), 400

        registration_document = None

        # Check if email is already in use
        existing_email_message = get_registration_conflict_message(email)
        if existing_email_message:
            return jsonify({'message': existing_email_message}), 400

        # Process registration in database
        with get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    # Check for duplicate student ID if provided
                    if student_id:
                        cur.execute("SELECT 1 FROM students WHERE student_number=%s", (student_id,))
                        if cur.fetchone():
                            return jsonify({'message': 'This ID number already exists.'}), 400
                        if column_exists('registration_requests', 'student_number'):
                            cur.execute("SELECT email, student_number FROM registration_requests WHERE student_number=%s LIMIT 1", (student_id,))
                            request_row = cur.fetchone()
                            if request_row:
                                if request_row.get('email') == email:
                                    return jsonify({'message': 'This form already exists.'}), 400
                                return jsonify({'message': 'This ID number already exists.'}), 400

                    # Save uploaded file only after initial validation and duplicate checks
                    if doc and doc.filename:
                        try:
                            original_name = secure_filename(doc.filename)
                            name_hash = hashlib.sha256(f"{original_name}:{datetime.utcnow().timestamp()}".encode('utf-8')).hexdigest()
                            extension = original_name.rsplit('.', 1)[1].lower() if '.' in original_name else 'bin'
                            filename = f"{name_hash}.{extension}"
                            file_path = os.path.join(UPLOAD_FOLDER, filename)
                            doc.save(file_path)
                            registration_document = filename
                            app.logger.info(f'Registration document saved: {filename}')
                        except Exception as e:
                            app.logger.error(f'File save failed: {str(e)}', exc_info=True)
                            return jsonify({'message': 'Failed to save registration document. Please try again.'}), 500

                    # Generate verification token
                    verification_token = generate_verification_token()

                    # Hash password with bcrypt
                    password_hash = hash_password(password)

                    # Insert registration request
                    cur.execute("""
                        INSERT INTO registration_requests 
                        (email, password_hash, full_name, student_number, registration_document, verification_token, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        email,
                        password_hash,
                        full_name,
                        student_id,
                        registration_document,
                        verification_token,
                        datetime.utcnow()
                    ))
                    
                    app.logger.info(f'Registration request created for email: {email}')

                except pymysql.IntegrityError as e:
                    app.logger.error(f'Database integrity error during registration: {str(e)}')
                    if 'email' in str(e).lower():
                        return jsonify({'message': 'Email already in use. Please use a different email address.'}), 400
                    elif 'student_number' in str(e).lower():
                        return jsonify({'message': 'Student ID already exists. Please use a different ID.'}), 400
                    return jsonify({'message': 'Registration failed due to duplicate data. Please check your information.'}), 400
                except pymysql.DatabaseError as e:
                    app.logger.error(f'Database error during registration: {str(e)}')
                    return jsonify({'message': 'Database error during registration. Please try again later.'}), 500
                except Exception as e:
                    app.logger.error(f'Unexpected error during registration: {str(e)}', exc_info=True)
                    return jsonify({'message': 'Unexpected error during registration. Please try again.'}), 500

            conn.commit()

        # Send verification email asynchronously (non-blocking)
        try:
            verification_url = url_for('verify_email', token=verification_token, _external=True)
            email_body = f"""Hello {full_name},

Thank you for registering with our online library system.

Please verify your email address by clicking the link below:
{verification_url}

If you did not create this account, please ignore this email.

Best regards,
Library Management System
"""
            email_body_html = f"""
            <html>
                <body style="font-family:Arial,Helvetica,sans-serif;background:#f4f7fb;color:#1f2937;padding:20px;">
                    <div style="max-width:600px;margin:0 auto;padding:30px;background:#ffffff;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
                        <h1 style="font-size:24px;margin-bottom:16px;color:#0f172a;">Verify your LIBRASYS account</h1>
                        <p style="font-size:16px;line-height:1.6;margin-bottom:24px;">Hello {full_name},</p>
                        <p style="font-size:16px;line-height:1.6;margin-bottom:24px;">Thank you for registering. Click the button below to confirm your email address and complete the verification process.</p>
                        <a href="{verification_url}" style="display:inline-block;padding:14px 24px;background:#0f766e;color:#ffffff;text-decoration:none;border-radius:8px;font-weight:600;">Verify Email</a>
                        <p style="font-size:14px;line-height:1.6;color:#475569;margin-top:24px;">If the button does not work, copy and paste the following link into your browser:</p>
                        <p style="font-size:14px;word-break:break-all;color:#2563eb;">{verification_url}</p>
                        <p style="font-size:14px;line-height:1.6;color:#475569;margin-top:24px;">If you did not register, please ignore this email.</p>
                        <p style="font-size:14px;line-height:1.6;color:#475569;margin-top:24px;">Best regards,<br/>Library Management System</p>
                    </div>
                </body>
            </html>
            """
            send_email_async('Verify Your Library Account', [email], email_body, email_body_html)
            app.logger.info(f'Verification email queued for student address: {email}')
            app.logger.info(f'Using SMTP sender account: {Config.MAIL_USERNAME}')
        except Exception as e:
            app.logger.warning(f'Email sending setup failed (non-blocking): {str(e)}')
            # Don't fail registration if email setup fails

        return jsonify({
            'message': 'Registration submitted successfully! Please check your email to verify your account. After verification, your registration will be reviewed by an admin or librarian for approval.',
            'requires_verification': True,
            'pending_approval': True,
            'email': email
        }), 201

    except Exception as e:
        app.logger.error(f'Unexpected error in register route: {str(e)}', exc_info=True)
        return jsonify({'message': 'An unexpected error occurred during registration. Please try again later.'}), 500



@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        user_input = data.get('username')
        password = data.get('password')

        error = validate_login(user_input, password)
        if error:
            return jsonify({'message': error}), 400

        user = find_account_by_identifier(user_input)
        if not user:
            return jsonify({'message': 'Invalid login credentials'}), 401

        stored_password = user.get('password_hash')
        password_ok = False
        if stored_password:
            password_ok = check_password(stored_password, password)

        if not password_ok:
            return jsonify({'message': 'Invalid login credentials'}), 401

        # Check status and email verification for students
        if user.get('role') == 'student':
            if user.get('status') != 'active':
                if user.get('status') == 'pending':
                    return jsonify({'message': 'Account is pending admin approval'}), 403
                elif user.get('status') == 'rejected':
                    return jsonify({'message': 'Account registration was rejected'}), 403
                elif user.get('status') == 'suspended':
                    return jsonify({'message': 'Account is suspended'}), 403
                else:
                    return jsonify({'message': 'Account is inactive'}), 403
            if not user.get('email_verified', 1):
                return jsonify({'message': 'Email address must be verified before logging in.'}), 403
        else:
            if user.get('status') != 'active':
                return jsonify({'message': 'Account is not active'}), 403

        token = create_access_token(identity=user['email'])

        return jsonify({
            'access_token': token,
            'role': user.get('role', 'student'),
            'message': 'Login successful'
        }), 200
    except pymysql.err.OperationalError as e:
        app.logger.error(f'Login database error: {str(e)}')
        return jsonify({
            'message': 'Database connection error. Please verify backend database credentials and configuration.',
            'error': str(e)
        }), 500
    except Exception as e:
        import traceback
        app.logger.error(f'Login error: {str(e)}\n{traceback.format_exc()}')
        return jsonify({'message': 'Login failed. Please try again.', 'error': str(e)}), 500


@app.route('/user', methods=['GET'])
@jwt_required()
def get_user():
    email = get_jwt_identity()

    user = find_account_by_email(email)
    if not user:
        return jsonify({}), 200

    safe_user = {
        'email': user.get('email'),
        'full_name': user.get('full_name'),
        'role': user.get('role'),
        'status': user.get('status'),
        'student_number': user.get('student_number'),
        'email_verified': user.get('email_verified', False)
    }
    return jsonify(safe_user), 200


# ─────────────────────────────
# Stats
# ─────────────────────────────
@app.route('/stats', methods=['GET'])
def get_stats():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Count total books
                cur.execute("SELECT COUNT(*) AS c FROM books")
                total_books = cur.fetchone()['c']

                # Count borrowed books
                cur.execute("SELECT COUNT(*) AS c FROM borrow_records WHERE status='borrowed'")
                borrowed_books = cur.fetchone()['c']
                
                # Available books = total - borrowed
                available_books = max(0, total_books - borrowed_books)

                # Count total students
                cur.execute("SELECT COUNT(*) AS c FROM students")
                total_members = cur.fetchone()['c']

        return jsonify({
            "total_books": total_books,
            "available_books": available_books,
            "borrowed_books": borrowed_books,
            "total_members": total_members
        }), 200
    except Exception as e:
        import traceback
        app.logger.error(f'Stats error: {str(e)}\n{traceback.format_exc()}')
        return jsonify({
            "total_books": 0,
            "available_books": 0,
            "borrowed_books": 0,
            "total_members": 0,
            "error": str(e)
        }), 500


# ─────────────────────────────
# Email Verification
# ─────────────────────────────
@app.route('/verify-email/<token>', methods=['GET'])
def verify_email(token):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT request_id, email, password_hash, full_name, student_number, registration_document FROM registration_requests WHERE verification_token=%s AND email_verified=0",
                (token,)
            )
            request_row = cur.fetchone()
            if not request_row:
                return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Verification Failed</title>
    <style>
        body { font-family: Arial, Helvetica, sans-serif; background:#f3f4f6; color:#111827; margin:0; padding:0; }
        .container { max-width:520px; margin:80px auto; padding:32px; background:#ffffff; border-radius:16px; box-shadow:0 16px 40px rgba(15,23,42,0.08); text-align:center; }
        h1 { margin-bottom:18px; font-size:28px; color:#111827; }
        p { margin-bottom:18px; line-height:1.7; color:#475569; }
        .button { display:inline-block; padding:12px 24px; background:#0f766e; color:#ffffff; border-radius:10px; text-decoration:none; font-weight:600; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Verification Failed</h1>
        <p>The verification link is invalid or has already been used. Please register again or contact support if you need help.</p>
    </div>
</body>
</html>''', 400

            student_number = request_row.get('student_number')
            if not student_number:
                student_number = f"STU{int(datetime.utcnow().timestamp() * 1000)}"

            while True:
                cur.execute("SELECT 1 FROM students WHERE student_number=%s", (student_number,))
                if not cur.fetchone():
                    break
                student_number = f"STU{int(datetime.utcnow().timestamp() * 1000)}"

            cur.execute(
                "INSERT INTO students (student_number, email, password_hash, full_name, status, email_verified, registration_document, created_at) VALUES (%s, %s, %s, %s, 'pending', TRUE, %s, %s)",
                (
                    student_number,
                    request_row['email'],
                    request_row['password_hash'],
                    request_row['full_name'],
                    request_row['registration_document'],
                    datetime.utcnow()
                )
            )

            cur.execute(
                "UPDATE registration_requests SET email_verified=1, verified_at=%s, verification_token=NULL WHERE request_id=%s",
                (datetime.utcnow(), request_row['request_id'])
            )
        conn.commit()

    return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Verified</title>
    <style>
        body { font-family: Arial, Helvetica, sans-serif; background:#f3f4f6; color:#111827; margin:0; padding:0; }
        .container { max-width:520px; margin:80px auto; padding:32px; background:#ffffff; border-radius:16px; box-shadow:0 16px 40px rgba(15,23,42,0.08); text-align:center; }
        h1 { margin-bottom:18px; font-size:28px; color:#111827; }
        p { margin-bottom:18px; line-height:1.7; color:#475569; }
        .button { display:inline-block; padding:12px 24px; background:#0f766e; color:#ffffff; border-radius:10px; text-decoration:none; font-weight:600; }
    </style>
</head>
<body>
    <div class="container">
        <h1>You are now verified.</h1>
        <p>Your email has been confirmed successfully. Please wait for approval by the admin before logging in.</p>
        <a href="/" class="button">Return to LIBRASYS</a>
    </div>
</body>
</html>''', 200


# ─────────────────────────────
# Forgot Password
# ─────────────────────────────
@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json() or {}
    email = data.get('email')
    if not email or not EMAIL_REGEX.match(email):
        return jsonify({'message': 'Valid email is required'}), 400

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT student_id, full_name FROM students WHERE email=%s AND status='active'", (email,))
            student = cur.fetchone()
            if not student:
                return jsonify({'message': 'No active account found with this email'}), 404

            reset_token = generate_verification_token()
            reset_expires = datetime.utcnow() + timedelta(hours=1)

            cur.execute(
                "UPDATE students SET reset_token=%s, reset_expires_at=%s WHERE student_id=%s",
                (reset_token, reset_expires, student['student_id'])
            )
        conn.commit()

        # Send reset email
        try:
            reset_url = url_for('reset_password_page', token=reset_token, _external=True)
            msg = Message('Password Reset Request',
                         sender=Config.MAIL_DEFAULT_SENDER,
                         recipients=[email])
            msg.body = f"""Hello {student['full_name']},

You requested a password reset for your library account.

Click the link below to reset your password (valid for 1 hour):
{reset_url}

If you did not request this, please ignore this email.

Best regards,
Library Management System
"""
            mail.send(msg)
        except Exception as e:
            print(f"Email sending failed: {e}")
            return jsonify({'message': 'Failed to send reset email'}), 500

    return jsonify({'message': 'Password reset link sent to your email'}), 200


@app.route('/reset-password/<token>', methods=['GET'])
def reset_password_page(token):
    # This could serve a simple HTML page for password reset
    # For now, return a message; frontend can handle the UI
    return jsonify({'message': 'Use this token to reset your password', 'token': token}), 200


@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json() or {}
    token = data.get('token')
    new_password = data.get('new_password')

    if not token or not new_password:
        return jsonify({'message': 'Token and new password are required'}), 400

    if not PASSWORD_REGEX.match(new_password):
        return jsonify({'message': 'Password must be at least 8 characters and include uppercase, lowercase, number, and special character'}), 400

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT student_id FROM students WHERE reset_token=%s AND reset_expires_at > %s",
                (token, datetime.utcnow())
            )
            student = cur.fetchone()
            if not student:
                return jsonify({'message': 'Invalid or expired reset token'}), 400

            hashed_password = hash_password(new_password)
            cur.execute(
                "UPDATE students SET password_hash=%s, reset_token=NULL, reset_expires_at=NULL WHERE student_id=%s",
                (hashed_password, student['student_id'])
            )
        conn.commit()

    return jsonify({'message': 'Password reset successfully'}), 200


# ─────────────────────────────
# Admin Registration Review
# ─────────────────────────────
@app.route('/admin/pending-registrations', methods=['GET'])
@jwt_required()
def get_pending_registrations():
    email = get_jwt_identity()
    if not is_admin_user(email):
        return jsonify({'message': 'Admin access required'}), 403

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT student_id, student_number, email, full_name, registration_document, created_at
                FROM students
                WHERE status='pending' AND email_verified=1
                ORDER BY created_at DESC
            """)
            pending_students = cur.fetchall()

    return jsonify(pending_students), 200


@app.route('/admin/review-registration/<int:student_id>', methods=['POST'])
@jwt_required()
def review_registration(student_id):
    email = get_jwt_identity()
    if not is_admin_user(email):
        return jsonify({'message': 'Admin access required'}), 403
    data = request.get_json() or {}
    action = data.get('action')  # 'approve' or 'reject'
    admin_notes = data.get('notes', '')

    if action not in ['approve', 'reject']:
        return jsonify({'message': 'Invalid action'}), 400

    new_status = 'active' if action == 'approve' else 'rejected'

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Update student status
            cur.execute(
                "UPDATE students SET status=%s WHERE student_id=%s AND status='pending'",
                (new_status, student_id)
            )
            if cur.rowcount == 0:
                return jsonify({'message': 'Student not found or not pending'}), 404

            # Log the action (optional - don't fail if logging fails)
            try:
                # Get librarian ID for logging
                cur.execute("SELECT id FROM librarians WHERE email=%s", (email,))
                librarian = cur.fetchone()
                if librarian:
                    cur.execute("""
                        INSERT INTO audit_logs (role, user_id, action)
                        VALUES ('librarian', %s, %s)
                    """, (librarian['id'], f'registration_{action}: student_id={student_id}, status={new_status}'))
            except Exception as e:
                app.logger.warning(f"Failed to log audit action: {str(e)}")

        conn.commit()

    # Send notification email
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT email, full_name FROM students WHERE student_id=%s", (student_id,))
                student = cur.fetchone()

        if student:
            msg = Message(f'Registration {action.title()}d',
                         sender=Config.MAIL_DEFAULT_SENDER,
                         recipients=[student['email']])
            if action == 'approve':
                msg.body = f"""Hello {student['full_name']},

Congratulations! Your library account registration has been approved.

You can now log in to the system using your email and password.

Best regards,
Library Management System
"""
            else:
                msg.body = f"""Hello {student['full_name']},

Unfortunately, your library account registration has been rejected.

Reason: {admin_notes}

If you believe this is an error, please contact the library administration.

Best regards,
Library Management System
"""
            mail.send(msg)
    except Exception as e:
        print(f"Notification email failed: {e}")

    return jsonify({'message': f'Registration {action}d successfully'}), 200


@app.route('/admin/student-document/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student_document(student_id):
    email = get_jwt_identity()
    if not is_admin_user(email):
        return jsonify({'message': 'Admin access required'}), 403

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT registration_document FROM students WHERE student_id=%s",
                (student_id,)
            )
            student = cur.fetchone()

    if not student or not student['registration_document']:
        return jsonify({'message': 'Document not found'}), 404

    file_path = os.path.join(UPLOAD_FOLDER, student['registration_document'])
    if not os.path.exists(file_path):
        return jsonify({'message': 'File not found'}), 404

    return send_from_directory(UPLOAD_FOLDER, student['registration_document'])


def get_current_user_and_student():
    email = get_jwt_identity()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM students WHERE email=%s", (email,))
            student = cur.fetchone()
            if not student:
                return None, None
    return student, student


def get_default_librarian_id():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT librarian_id FROM librarians LIMIT 1")
            row = cur.fetchone()
            return row['librarian_id'] if row else None


@app.route('/books', methods=['GET'])
def list_books():
    book_id_col = get_books_id_column()
    inventory_columns = get_book_inventory_select_columns()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {book_id_col} AS book_id, isbn, title, author, category, image_url, {inventory_columns}, created_at "
                f"FROM books ORDER BY {book_id_col} DESC"
            )
            books = cur.fetchall()
    return jsonify(books), 200


@app.route('/borrowings', methods=['GET'])
@jwt_required()
def list_borrowings():
    book_id_col = get_books_id_column()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT br.borrow_id, br.student_id, br.book_id, br.borrow_date, br.due_date, br.return_date, br.status, br.notes, br.fine_amount, br.fine_paid, br.renewal_count, br.last_renewal_date, b.title AS book_title, b.category, s.email AS student_email "
                f"FROM borrow_records br "
                f"JOIN students s ON br.student_id=s.student_id "
                f"JOIN books b ON br.book_id=b.{book_id_col} "
                f"ORDER BY br.borrow_date DESC"
            )
            borrowings = cur.fetchall()
    return jsonify(borrowings), 200


@app.route('/borrowings/<int:borrow_id>/renew', methods=['POST'])
@jwt_required()
def renew_borrowing(borrow_id):
    user, student = get_current_user_and_student()
    if not user or not student:
        return jsonify({'message': 'Student account not found'}), 404

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT borrow_id, student_id, due_date, status, renewal_count FROM borrow_records WHERE borrow_id=%s AND student_id=%s",
                (borrow_id, student['student_id'])
            )
            record = cur.fetchone()
            if not record:
                return jsonify({'message': 'Borrow record not found'}), 404
            if record['status'] != 'borrowed':
                return jsonify({'message': 'Only currently borrowed books can be renewed'}), 400

            due_date = record.get('due_date')
            if due_date is None:
                return jsonify({'message': 'Invalid due date'}), 400

            if due_date < datetime.utcnow().date():
                return jsonify({'message': 'Book is overdue and cannot be renewed'}), 400

            renewal_count = record.get('renewal_count') or 0
            if renewal_count >= 3:
                return jsonify({'message': 'Renewal limit reached'}), 400

            new_due_date = due_date + timedelta(days=14)
            cur.execute(
                "UPDATE borrow_records SET due_date=%s, renewal_count=%s, last_renewal_date=%s WHERE borrow_id=%s",
                (new_due_date, renewal_count + 1, datetime.utcnow().date(), borrow_id)
            )
        conn.commit()

    return jsonify({
        'message': 'Book renewed successfully.',
        'borrow_id': borrow_id,
        'new_due_date': new_due_date.isoformat(),
        'renewal_count': renewal_count + 1
    }), 200


@app.route('/student/profile', methods=['GET', 'PUT'])
@jwt_required()
def student_profile():
    user, student = get_current_user_and_student()
    if not user or not student:
        return jsonify({'message': 'Student profile not found'}), 404

    if request.method == 'GET':
        profile = {
            'full_name': student.get('fullname'),
            'email': student.get('email'),
            'student_number': student.get('student_number'),
            'course': student.get('course'),
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
            cur.execute("UPDATE students SET phone=%s, address=%s WHERE student_id=%s", (phone, address, student['student_id']))
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

    book_id_col = get_books_id_column()
    book_where = 'book_id' if book_id_col == 'book_id' else book_id_col

    with get_connection() as conn:
        with conn.cursor() as cur:
            has_available_copies = column_exists('books', 'available_copies')
            select_columns = 'available_copies, status' if has_available_copies else 'status'
            cur.execute(f"SELECT {select_columns} FROM books WHERE {book_where}=%s", (book_id,))
            book = cur.fetchone()
            if not book:
                return jsonify({'message': 'Book not found'}), 404
            if has_available_copies:
                if book['available_copies'] <= 0:
                    return jsonify({'message': 'Book is not available'}), 400
            else:
                if (book.get('status') or 'available') != 'available':
                    return jsonify({'message': 'Book is not available'}), 400

            librarian_id = get_default_librarian_id() or 1
            borrow_date = datetime.utcnow().date().isoformat()

            cur.execute(
                "INSERT INTO borrow_records (student_id, book_id, librarian_id, borrow_date, due_date, status) VALUES (%s, %s, %s, %s, %s, 'borrowed')",
                (student['student_id'], book_id, librarian_id, borrow_date, due_date)
            )
            cur.execute(f"UPDATE books SET status='borrowed' WHERE {book_where}=%s", (book_id,))
            if has_available_copies:
                cur.execute(f"UPDATE books SET available_copies = available_copies - 1 WHERE {book_where}=%s", (book_id,))
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
            book_id_col = get_books_id_column()
            book_where = 'book_id' if book_id_col == 'book_id' else book_id_col

            cur.execute(
                f"SELECT br.*, b.{book_id_col} AS book_table_id, b.status AS book_status "
                f"FROM borrow_records br "
                f"JOIN books b ON br.book_id = b.{book_id_col} "
                f"WHERE br.borrow_id=%s AND br.student_id=%s",
                (borrow_id, student['student_id'])
            )
            record = cur.fetchone()
            if not record:
                return jsonify({'message': 'Borrow record not found'}), 404
            if record['status'] == 'returned':
                return jsonify({'message': 'Book already returned'}), 400

            return_date = datetime.utcnow().date()
            due_date = record['due_date']

            # Calculate fine if overdue
            fine_amount = 0.00
            if return_date > due_date:
                days_overdue = (return_date - due_date).days
                fine_amount = days_overdue * 10.00

            try:
                cur.execute(
                    "UPDATE borrow_records SET status='returned', return_date=%s, fine_amount=%s WHERE borrow_id=%s",
                    (return_date.isoformat(), fine_amount, borrow_id)
                )

                # Mark the returned book as available again
                cur.execute(
                    f"UPDATE books SET status='available' WHERE {book_where}=%s",
                    (record['book_table_id'],)
                )

                if column_exists('books', 'available_copies'):
                    cur.execute(
                        f"UPDATE books SET available_copies = LEAST(available_copies + 1, total_copies) WHERE {book_where}=%s",
                        (record['book_table_id'],)
                    )

                if column_exists('students', 'borrowed_books_count'):
                    cur.execute(
                        "UPDATE students SET borrowed_books_count = GREATEST(borrowed_books_count - 1, 0) WHERE student_id=%s",
                        (student['student_id'],)
                    )

                # Create fine record if applicable
                if fine_amount > 0:
                    cur.execute(
                        "INSERT INTO fines (borrow_id, student_id, amount, reason, status, issued_date) VALUES (%s, %s, %s, %s, %s, %s)",
                        (borrow_id, student['student_id'], fine_amount, 'Overdue book return', 'pending', return_date.isoformat())
                    )
            except Exception as e:
                conn.rollback()
                app.logger.error(f"Return transaction failed for borrow_id={borrow_id}: {str(e)}")
                return jsonify({'message': 'Unable to process return at this time. Please try again later.'}), 500

        conn.commit()

    response = {
        'message': 'Book returned successfully.',
        'borrow_id': borrow_id,
        'book_id': record['book_table_id'],
        'return_date': return_date.isoformat()
    }
    if fine_amount > 0:
        response['fine_amount'] = fine_amount

    return jsonify(response), 200


@app.route('/student/fines', methods=['GET'])
@jwt_required()
def get_fines():
    user, student = get_current_user_and_student()
    if not user or not student:
        return jsonify({'message': 'Student account not found'}), 404

    book_id_col = get_books_id_column()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT f.fine_id, f.amount, f.reason, f.status, f.issued_date, f.paid_date, b.title AS book_title, br.borrow_id "
                f"FROM fines f "
                f"LEFT JOIN borrow_records br ON f.borrow_id=br.borrow_id "
                f"LEFT JOIN books b ON br.book_id=b.{book_id_col} "
                f"WHERE f.student_id=%s "
                f"ORDER BY f.issued_date DESC",
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


# ─────────────────────────────
# Student Dashboard Book Management
# ─────────────────────────────

@app.route('/student/books/search', methods=['GET'])
@jwt_required()
def search_books():
    """
    Search books with filters for title, author, category, and ISBN.
    Returns books with ISBN included in all responses.
    """
    user, student = get_current_user_and_student()
    if not user or not student:
        return jsonify({'message': 'Student account not found'}), 404

    # Get query parameters
    title = request.args.get('title', '').strip()
    author = request.args.get('author', '').strip()
    category = request.args.get('category', '').strip()
    isbn = request.args.get('isbn', '').strip()
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)

    # Validate limit and offset
    if limit < 1 or limit > 100:
        limit = 50
    if offset < 0:
        offset = 0

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Build WHERE clause dynamically
            where_conditions = []
            params = []

            if title:
                where_conditions.append("title LIKE %s")
                params.append(f"%{title}%")

            if author:
                where_conditions.append("author LIKE %s")
                params.append(f"%{author}%")

            if category:
                where_conditions.append("category LIKE %s")
                params.append(f"%{category}%")

            if isbn:
                where_conditions.append("isbn LIKE %s")
                params.append(f"%{isbn}%")

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # Execute search query
            book_id_col = get_books_id_column()
            inventory_columns = get_book_inventory_select_columns()
            query = f"""
                SELECT {book_id_col} AS book_id,
                       isbn,
                       title,
                       author,
                       category,
                       image_url,
                       {inventory_columns},
                       created_at
                FROM books
                WHERE {where_clause}
                ORDER BY title ASC
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])

            cur.execute(query, params)
            books = cur.fetchall()

            # Get total count for pagination
            count_query = f"SELECT COUNT(*) as total FROM books WHERE {where_clause}"
            cur.execute(count_query, params[:-2])  # Remove limit and offset for count
            total_count = cur.fetchone()['total']

    return jsonify({
        'books': books,
        'pagination': {
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + limit) < total_count
        }
    }), 200


@app.route('/student/books/<isbn>/borrow', methods=['POST'])
@jwt_required()
def borrow_book_by_isbn(isbn):
    """
    Borrow a book by ISBN. Updates book status to 'borrowed',
    stores student info and timestamp. Prevents duplicate borrowing.
    """
    user, student = get_current_user_and_student()
    if not user or not student:
        return jsonify({'message': 'Student account not found'}), 404

    if not isbn or len(isbn.strip()) < 10:
        return jsonify({'message': 'Valid ISBN is required'}), 400

    isbn = isbn.strip()

    # Check if student has reached borrowing limit (max 5 books)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as borrowed_count FROM borrow_records WHERE student_id=%s AND status='borrowed'", (student['student_id'],))
            borrowed_count = cur.fetchone()['borrowed_count']
            
            if borrowed_count >= 5:
                return jsonify({'message': 'You have reached the maximum borrowing limit of 5 books'}), 400

            # Find book by ISBN
            book_id_col = get_books_id_column()
            cur.execute(f"SELECT {book_id_col} AS book_id, title, status FROM books WHERE isbn=%s", (isbn,))
            book = cur.fetchone()

            if not book:
                return jsonify({'message': 'Book not found'}), 404

            if book['status'] != 'available':
                return jsonify({'message': 'Book is not available for borrowing'}), 400

            # Check if student already borrowed this book
            cur.execute(
                "SELECT borrow_id FROM borrow_records WHERE student_id=%s AND book_id=%s AND status='borrowed'",
                (student['student_id'], book['book_id'])
            )
            existing_borrow = cur.fetchone()

            if existing_borrow:
                return jsonify({'message': 'You have already borrowed this book'}), 400

            # Check if student has any overdue books
            cur.execute(
                "SELECT COUNT(*) as overdue_count FROM borrow_records WHERE student_id=%s AND status='borrowed' AND due_date < CURDATE()",
                (student['student_id'],)
            )
            overdue_count = cur.fetchone()['overdue_count']

            if overdue_count > 0:
                return jsonify({'message': 'You have overdue books. Please return them before borrowing new books.'}), 400

            # Proceed with borrowing
            borrow_date = datetime.utcnow().date()
            due_date = borrow_date + timedelta(days=14)  # 14 days borrowing period

            try:
                cur.execute(
                    "INSERT INTO borrow_records (student_id, book_id, borrow_date, due_date, status) VALUES (%s, %s, %s, %s, 'borrowed')",
                    (student['student_id'], book['book_id'], borrow_date, due_date)
                )

                # Update book status to borrowed
                cur.execute(f"UPDATE books SET status='borrowed' WHERE {book_id_col}=%s", (book['book_id'],))

                if column_exists('books', 'available_copies'):
                    cur.execute(
                        f"UPDATE books SET available_copies = GREATEST(available_copies - 1, 0) WHERE {book_id_col}=%s",
                        (book['book_id'],)
                    )

                conn.commit()

            except Exception as e:
                conn.rollback()
                app.logger.error(f"Borrow transaction failed: {str(e)}")
                return jsonify({'message': 'Failed to borrow book. Please try again.'}), 500

    return jsonify({
        'message': 'Book borrowed successfully',
        'book_title': book['title'],
        'isbn': isbn,
        'due_date': due_date.isoformat(),
        'borrow_date': borrow_date.isoformat()
    }), 200


@app.route('/student/books/<isbn>/return', methods=['POST'])
@jwt_required()
def return_book_by_isbn(isbn):
    """
    Return a book by ISBN. Updates book status to 'available'
    and restores book availability.
    """
    user, student = get_current_user_and_student()
    if not user or not student:
        return jsonify({'message': 'Student account not found'}), 404

    if not isbn or len(isbn.strip()) < 10:
        return jsonify({'message': 'Valid ISBN is required'}), 400

    isbn = isbn.strip()

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Find book by ISBN and get borrow record
            book_id_col = get_books_id_column()
            cur.execute(f"""
                SELECT br.borrow_id, br.book_id, br.due_date, b.title, b.{book_id_col} AS book_table_id
                FROM borrow_records br
                JOIN books b ON br.book_id = b.{book_id_col}
                WHERE br.student_id=%s AND b.isbn=%s AND br.status='borrowed'
            """, (student['student_id'], isbn))

            borrow_record = cur.fetchone()

            if not borrow_record:
                return jsonify({'message': 'No active borrowing record found for this book'}), 404

            return_date = datetime.utcnow().date()

            try:
                # Update borrow record
                cur.execute(
                    "UPDATE borrow_records SET status='returned', return_date=%s WHERE borrow_id=%s",
                    (return_date, borrow_record['borrow_id'])
                )

                # Update book status to available
                cur.execute(f"UPDATE books SET status='available' WHERE {book_id_col}=%s", (borrow_record['book_table_id'],))

                if column_exists('books', 'available_copies'):
                    cur.execute(
                        f"UPDATE books SET available_copies = LEAST(available_copies + 1, total_copies) WHERE {book_id_col}=%s",
                        (borrow_record['book_table_id'],)
                    )

                # Check if book was returned late and calculate fine if needed
                fine_amount = 0.0
                if return_date > borrow_record['due_date']:
                    days_overdue = (return_date - borrow_record['due_date']).days
                    fine_amount = days_overdue * 0.50  # $0.50 per day overdue

                    if fine_amount > 0:
                        cur.execute(
                            "INSERT INTO fines (borrow_id, student_id, amount, reason, status, issued_date) VALUES (%s, %s, %s, %s, 'pending', %s)",
                            (borrow_record['borrow_id'], student['student_id'], fine_amount, f'Overdue book - {days_overdue} days late', return_date)
                        )

                conn.commit()

            except Exception as e:
                conn.rollback()
                app.logger.error(f"Return transaction failed: {str(e)}")
                return jsonify({'message': 'Failed to return book. Please try again.'}), 500

    response = {
        'message': 'Book returned successfully',
        'book_title': borrow_record['title'],
        'isbn': isbn,
        'return_date': return_date.isoformat()
    }

    if fine_amount > 0:
        response['fine_assessed'] = fine_amount
        response['message'] += f' A fine of ${fine_amount:.2f} has been assessed for late return.'

    return jsonify(response), 200


@app.route('/student/my-books', methods=['GET'])
@jwt_required()
def get_my_borrowed_books():
    """
    Get list of books currently borrowed by the student.
    """
    user, student = get_current_user_and_student()
    if not user or not student:
        return jsonify({'message': 'Student account not found'}), 404

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT br.borrow_id, br.borrow_date, br.due_date, br.status,
                       b.id AS book_id, b.isbn, b.title, b.author, b.category, b.image_url
                FROM borrow_records br
                JOIN books b ON br.book_id = b.id
                WHERE br.student_id=%s AND br.status='borrowed'
                ORDER BY br.due_date ASC
            """, (student['student_id'],))

            borrowed_books = cur.fetchall()

            # Add overdue status
            current_date = datetime.utcnow().date()
            for book in borrowed_books:
                book['is_overdue'] = book['due_date'] < current_date
                book['days_until_due'] = (book['due_date'] - current_date).days

    return jsonify({
        'borrowed_books': borrowed_books,
        'total_borrowed': len(borrowed_books)
    }), 200


@app.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    email = get_jwt_identity()
    if not is_admin_user(email):
        return jsonify({'message': 'Admin access required'}), 403

    with get_connection() as conn:
        with conn.cursor() as cur:
            queries = []
            admin_key = get_table_primary_key('admins', ['id', 'admin_id'])
            librarian_key = get_table_primary_key('librarians', ['id', 'librarian_id'])
            student_key = get_table_primary_key('students', ['student_id', 'user_id'])

            if admin_key:
                queries.append(
                    f"SELECT {admin_key} AS user_id, email, fullname AS full_name, 'admin' AS role, COALESCE(status, 'active') AS status FROM admins"
                )
            if librarian_key:
                queries.append(
                    f"SELECT {librarian_key} AS user_id, email, fullname AS full_name, 'librarian' AS role, COALESCE(status, 'active') AS status FROM librarians"
                )
            if student_key:
                queries.append(
                    f"SELECT {student_key} AS user_id, email, full_name, 'student' AS role, COALESCE(status, 'pending') AS status FROM students"
                )

            if not queries:
                users = []
            else:
                cur.execute(' UNION ALL '.join(queries) + ' ORDER BY role, email')
                users = cur.fetchall()
    return jsonify(users), 200


@app.route('/users/<int:user_id>/status', methods=['PUT'])
@jwt_required()
def update_user_status(user_id):
    email = get_jwt_identity()
    if not is_admin_user(email):
        return jsonify({'message': 'Admin access required'}), 403

    data = request.get_json() or {}
    new_status = data.get('status')
    if new_status not in ['active', 'inactive', 'suspended', 'pending', 'rejected']:
        return jsonify({'message': 'Invalid status'}), 400

    with get_connection() as conn:
        with conn.cursor() as cur:
            updated = False

            try:
                cur.execute("UPDATE users SET status=%s WHERE user_id=%s", (new_status, user_id))
                updated = updated or cur.rowcount > 0
            except Exception:
                pass

            cur.execute("UPDATE students SET status=%s WHERE student_id=%s", (new_status, user_id))
            updated = updated or cur.rowcount > 0

            try:
                cur.execute("UPDATE admins SET status=%s WHERE id=%s", (new_status, user_id))
                updated = updated or cur.rowcount > 0
            except Exception:
                pass

            try:
                cur.execute("UPDATE librarians SET status=%s WHERE id=%s", (new_status, user_id))
                updated = updated or cur.rowcount > 0
            except Exception:
                pass

            if not updated:
                return jsonify({'message': 'User not found'}), 404

        conn.commit()

    return jsonify({'message': 'User status updated successfully'}), 200


@app.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    email = get_jwt_identity()
    if not is_admin_user(email):
        return jsonify({'message': 'Admin access required'}), 403

    with get_connection() as conn:
        with conn.cursor() as cur:
            deleted = False
            admin_key = get_table_primary_key('admins', ['id', 'admin_id'])
            librarian_key = get_table_primary_key('librarians', ['id', 'librarian_id'])
            student_key = get_table_primary_key('students', ['student_id', 'user_id'])

            if admin_key:
                deleted = delete_by_key(cur, 'admins', admin_key, user_id) or deleted

            if not deleted and librarian_key:
                deleted = delete_by_key(cur, 'librarians', librarian_key, user_id) or deleted

            if student_key:
                # Remove student-linked records first
                delete_by_key(cur, 'fines', 'student_id', user_id)
                delete_by_key(cur, 'borrow_records', 'student_id', user_id)
                deleted = delete_by_key(cur, 'students', student_key, user_id) or deleted

            if table_exists('users'):
                deleted = delete_by_key(cur, 'users', 'user_id', user_id) or deleted

            if not deleted:
                return jsonify({'message': 'User not found'}), 404

        conn.commit()

    return jsonify({'message': 'User deleted successfully'}), 200


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
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    app.run(debug=True, host=host, port=port)