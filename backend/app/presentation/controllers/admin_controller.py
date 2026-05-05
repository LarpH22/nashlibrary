import os
import re
from datetime import datetime

from flask import jsonify, request, send_from_directory, url_for
from flask_jwt_extended import get_jwt

from ...domain.services.auth_service import AuthService
from ...domain.services.validation_service import ValidationService
from ...infrastructure.config import Config
from ...infrastructure.database.db_connection import get_connection
from ...infrastructure.repositories_impl.inventory_schema import ensure_inventory_schema
from ...infrastructure.repositories_impl.auth_repository_impl import AdminAuthRepositoryImpl, LibrarianAuthRepositoryImpl
from ...infrastructure.repositories_impl.loan_repository_impl import LoanRepositoryImpl


class AdminController:
    def __init__(self):
        self.admin_repo = AdminAuthRepositoryImpl()
        self.librarian_repo = LibrarianAuthRepositoryImpl()
        self.auth_service = AuthService(self.admin_repo, self.librarian_repo, self.admin_repo)
        self.validation_service = ValidationService()
        self.loan_repository = LoanRepositoryImpl()

    def _validate_new_password(self, new_password, confirm_password=None):
        valid, message = self.validation_service.validate_password_strength(new_password)
        if not valid:
            return message
        if confirm_password is not None and not confirm_password:
            return 'Confirm password is required'
        if confirm_password is not None and new_password != confirm_password:
            return 'Passwords do not match'
        return None

    def _validate_password_change(self, old_password, new_password, confirm_password=None):
        valid, message = self.validation_service.validate_password_change(old_password, new_password, confirm_password)
        return None if valid else message

    def _require_admin(self):
        jwt_claims = get_jwt()
        if jwt_claims.get('role') != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        return None

    def _require_admin_or_librarian(self):
        jwt_claims = get_jwt()
        if jwt_claims.get('role') not in ['admin', 'librarian']:
            return jsonify({'message': 'Admin or librarian access required'}), 403
        return None

    def _attach_student_document_state(self, student):
        document_name = student.get('registration_document')
        if not document_name:
            student['document_exists'] = False
            return student

        document_path = os.path.abspath(os.path.join(Config.UPLOAD_FOLDER, os.path.basename(document_name)))
        upload_root = os.path.abspath(Config.UPLOAD_FOLDER)
        document_exists = document_path.startswith(upload_root) and os.path.exists(document_path)
        student['document_exists'] = document_exists
        if document_exists:
            student['document_url'] = url_for('admin.get_student_document', student_id=student['student_id'])
        return student

    def _parse_pagination_params(self):
        page = request.args.get('page', type=int)
        limit = request.args.get('limit', type=int)
        paginate = page is not None or limit is not None
        page = page if page and page > 0 else 1
        limit = limit if limit and limit > 0 else 15
        offset = (page - 1) * limit
        return page, limit, offset, paginate

    def list_categories(self):
        auth_error = self._require_admin()
        if auth_error:
            return auth_error

        page, limit, offset, paginate = self._parse_pagination_params()
        search = (request.args.get('search') or '').strip()

        with get_connection() as conn:
            with conn.cursor() as cur:
                if paginate:
                    if search:
                        cur.execute('SELECT COUNT(*) AS total FROM categories WHERE name LIKE %s', (f'%{search}%',))
                    else:
                        cur.execute('SELECT COUNT(*) AS total FROM categories')
                    total = cur.fetchone().get('total', 0)

                    if search:
                        cur.execute('SELECT category_id, name FROM categories WHERE name LIKE %s ORDER BY name ASC LIMIT %s OFFSET %s', (f'%{search}%', limit, offset))
                    else:
                        cur.execute('SELECT category_id, name FROM categories ORDER BY name ASC LIMIT %s OFFSET %s', (limit, offset))
                    categories = cur.fetchall()

                    return jsonify({
                        'categories': categories,
                        'pagination': {
                            'page': page,
                            'limit': limit,
                            'total': total,
                            'total_pages': max(1, (total + limit - 1) // limit)
                        }
                    }), 200
                else:
                    if search:
                        cur.execute('SELECT category_id, name FROM categories WHERE name LIKE %s ORDER BY name ASC', (f'%{search}%',))
                    else:
                        cur.execute('SELECT category_id, name FROM categories ORDER BY name ASC')
                    categories = cur.fetchall()
        return jsonify(categories), 200

    def add_category(self):
        auth_error = self._require_admin()
        if auth_error:
            return auth_error

        data = request.get_json() or {}
        name = data.get('name', '').strip()
        if not name:
            return jsonify({'message': 'Category name is required'}), 400

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('INSERT IGNORE INTO categories (name, created_at) VALUES (%s, NOW())', (name,))
                conn.commit()
                category_id = cur.lastrowid
                if category_id == 0:
                    cur.execute('SELECT category_id FROM categories WHERE name=%s LIMIT 1', (name,))
                    existing = cur.fetchone()
                    category_id = existing.get('category_id') if existing else None

        return jsonify({'message': 'Category saved', 'category_id': category_id}), 201

    def delete_category(self, category_id):
        auth_error = self._require_admin()
        if auth_error:
            return auth_error

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM categories WHERE category_id=%s', (category_id,))
                conn.commit()
                deleted = cur.rowcount
        if not deleted:
            return jsonify({'message': 'Category not found'}), 404
        return jsonify({'message': 'Category deleted'}), 200

    def list_authors(self):
        auth_error = self._require_admin()
        if auth_error:
            return auth_error

        page, limit, offset, paginate = self._parse_pagination_params()
        search = (request.args.get('search') or '').strip()

        with get_connection() as conn:
            with conn.cursor() as cur:
                if paginate:
                    if search:
                        cur.execute('SELECT COUNT(*) AS total FROM authors WHERE name LIKE %s', (f'%{search}%',))
                    else:
                        cur.execute('SELECT COUNT(*) AS total FROM authors')
                    total = cur.fetchone().get('total', 0)

                    if search:
                        cur.execute('SELECT author_id, name FROM authors WHERE name LIKE %s ORDER BY name ASC LIMIT %s OFFSET %s', (f'%{search}%', limit, offset))
                    else:
                        cur.execute('SELECT author_id, name FROM authors ORDER BY name ASC LIMIT %s OFFSET %s', (limit, offset))
                    authors = cur.fetchall()

                    return jsonify({
                        'authors': authors,
                        'pagination': {
                            'page': page,
                            'limit': limit,
                            'total': total,
                            'total_pages': max(1, (total + limit - 1) // limit)
                        }
                    }), 200
                else:
                    if search:
                        cur.execute('SELECT author_id, name FROM authors WHERE name LIKE %s ORDER BY name ASC', (f'%{search}%',))
                    else:
                        cur.execute('SELECT author_id, name FROM authors ORDER BY name ASC')
                    authors = cur.fetchall()
        return jsonify(authors), 200

    def add_author(self):
        auth_error = self._require_admin()
        if auth_error:
            return auth_error

        data = request.get_json() or {}
        name = data.get('name', '').strip()
        if not name:
            return jsonify({'message': 'Author name is required'}), 400

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('INSERT IGNORE INTO authors (name, created_at) VALUES (%s, NOW())', (name,))
                conn.commit()
                author_id = cur.lastrowid
                if author_id == 0:
                    cur.execute('SELECT author_id FROM authors WHERE name=%s LIMIT 1', (name,))
                    existing = cur.fetchone()
                    author_id = existing.get('author_id') if existing else None

        return jsonify({'message': 'Author saved', 'author_id': author_id}), 201

    def delete_author(self, author_id):
        auth_error = self._require_admin()
        if auth_error:
            return auth_error

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM authors WHERE author_id=%s', (author_id,))
                conn.commit()
                deleted = cur.rowcount
        if not deleted:
            return jsonify({'message': 'Author not found'}), 404
        return jsonify({'message': 'Author deleted'}), 200

    def search_student(self, student_id):
        auth_error = self._require_admin_or_librarian()
        if auth_error:
            return auth_error

        with get_connection() as conn:
            with conn.cursor() as cur:
                if str(student_id).isdigit():
                    cur.execute(
                        """
                        SELECT student_id, email, full_name, student_number, department,
                               year_level, status, email_verified, registration_document,
                               last_login, created_at, updated_at
                        FROM students
                        WHERE student_id=%s OR student_number=%s
                        LIMIT 1
                        """,
                        (int(student_id), student_id)
                    )
                else:
                    cur.execute(
                        """
                        SELECT student_id, email, full_name, student_number, department,
                               year_level, status, email_verified, registration_document,
                               last_login, created_at, updated_at
                        FROM students
                        WHERE student_number=%s
                        LIMIT 1
                        """,
                        (student_id,)
                    )
                student = cur.fetchone()
                if not student:
                    return jsonify({'message': 'Student not found'}), 404

                cur.execute(
                    'SELECT borrow_id, book_id, student_id, borrow_date, due_date, return_date, status FROM borrow_records WHERE student_id=%s ORDER BY borrow_date DESC',
                    (student['student_id'],)
                )
                loans = cur.fetchall()

        self._attach_student_document_state(student)
        student['loans'] = loans
        return jsonify(student), 200

    def list_students(self):
        auth_error = self._require_admin_or_librarian()
        if auth_error:
            return auth_error

        page, limit, offset, paginate = self._parse_pagination_params()
        with get_connection() as conn:
            with conn.cursor() as cur:
                if paginate:
                    cur.execute('SELECT COUNT(*) AS total FROM students')
                    total = cur.fetchone().get('total', 0)
                    cur.execute(
                        """
                        SELECT
                            student_id,
                            student_id AS user_id,
                            email,
                            full_name,
                            student_number,
                            department,
                            year_level,
                            status,
                            email_verified,
                            registration_document,
                            last_login,
                            created_at,
                            updated_at
                        FROM students
                        ORDER BY full_name ASC
                        LIMIT %s OFFSET %s
                        """,
                        (limit, offset),
                    )
                else:
                    total = None
                    cur.execute(
                        """
                        SELECT
                            student_id,
                            student_id AS user_id,
                            email,
                            full_name,
                            student_number,
                            department,
                            year_level,
                            status,
                            email_verified,
                            registration_document,
                            last_login,
                            created_at,
                            updated_at
                        FROM students
                        ORDER BY full_name ASC
                        """
                    )
                students = cur.fetchall()
                for student in students:
                    self._attach_student_document_state(student)

        if paginate:
            return jsonify({
                'students': students,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'total_pages': max(1, (total + limit - 1) // limit)
                }
            }), 200

        return jsonify(students), 200

    def update_student(self, student_id):
        auth_error = self._require_admin()
        if auth_error:
            return auth_error

        try:
            student_id = int(student_id)
        except (TypeError, ValueError):
            return jsonify({'message': 'Invalid student ID'}), 400

        data = request.get_json() or {}
        full_name = str(data.get('full_name') or '').strip()
        email = str(data.get('email') or '').strip().lower()
        student_number = str(data.get('student_number') or '').strip()
        department = str(data.get('department') or '').strip() or None
        year_level = data.get('year_level')
        status = str(data.get('status') or '').strip().lower()
        email_verified = data.get('email_verified')

        if not full_name:
            return jsonify({'message': 'Full name is required'}), 400
        if len(full_name) > 100:
            return jsonify({'message': 'Full name must be 100 characters or fewer'}), 400
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            return jsonify({'message': 'A valid email is required'}), 400
        if not re.match(r'^\d{3}-\d{4}$', student_number):
            return jsonify({'message': 'Student ID must use format 241-0449'}), 400
        if status not in ['active', 'inactive', 'suspended', 'pending']:
            return jsonify({'message': 'Invalid account status'}), 400
        if year_level in (None, ''):
            year_level = None
        else:
            try:
                year_level = int(year_level)
            except (TypeError, ValueError):
                return jsonify({'message': 'Year level must be a number'}), 400
            if year_level < 1 or year_level > 6:
                return jsonify({'message': 'Year level must be between 1 and 6'}), 400

        email_verified = bool(email_verified)

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT student_id FROM students WHERE student_id=%s LIMIT 1', (student_id,))
                if not cur.fetchone():
                    return jsonify({'message': 'Student not found'}), 404

                cur.execute('SELECT student_id FROM students WHERE email=%s AND student_id<>%s LIMIT 1', (email, student_id))
                if cur.fetchone():
                    return jsonify({'message': 'Email is already used by another student'}), 409

                cur.execute('SELECT student_id FROM students WHERE student_number=%s AND student_id<>%s LIMIT 1', (student_number, student_id))
                if cur.fetchone():
                    return jsonify({'message': 'Student ID is already used by another student'}), 409

                cur.execute(
                    """
                    UPDATE students
                    SET full_name=%s,
                        email=%s,
                        student_number=%s,
                        department=%s,
                        year_level=%s,
                        status=%s,
                        email_verified=%s,
                        updated_at=NOW()
                    WHERE student_id=%s
                    """,
                    (full_name, email, student_number, department, year_level, status, email_verified, student_id),
                )
                conn.commit()

        return self.search_student(str(student_id))

    def reset_student_password(self, student_id):
        auth_error = self._require_admin()
        if auth_error:
            return auth_error

        try:
            student_id = int(student_id)
        except (TypeError, ValueError):
            return jsonify({'message': 'Invalid student ID'}), 400

        data = request.get_json() or {}
        new_password = str(data.get('new_password') or '')
        confirm_password = data.get('confirm_password', '')
        password_error = self._validate_new_password(new_password, confirm_password)
        if password_error:
            return jsonify({'message': password_error}), 400

        password_hash = self.auth_service.hash_password(new_password)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE students
                    SET password_hash=%s,
                        reset_token=NULL,
                        reset_expires_at=NULL,
                        updated_at=NOW()
                    WHERE student_id=%s
                    """,
                    (password_hash, student_id),
                )
                conn.commit()
                if cur.rowcount == 0:
                    return jsonify({'message': 'Student not found'}), 404

        return jsonify({'message': 'Student password reset successfully'}), 200

    def get_student_document(self, student_id):
        auth_error = self._require_admin()
        if auth_error:
            return auth_error

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT registration_document FROM students WHERE student_id=%s LIMIT 1', (student_id,))
                student = cur.fetchone()

        if not student:
            return jsonify({'message': 'Student not found'}), 404
        document_name = student.get('registration_document')
        if not document_name:
            return jsonify({'message': 'No registration document uploaded'}), 404

        document_name = os.path.basename(document_name)
        file_path = os.path.abspath(os.path.join(Config.UPLOAD_FOLDER, document_name))
        upload_root = os.path.abspath(Config.UPLOAD_FOLDER)
        if not file_path.startswith(upload_root):
            return jsonify({'message': 'Invalid registration document path'}), 400
        if not os.path.exists(file_path):
            return jsonify({
                'message': 'Registration document file is missing on the server',
                'filename': document_name
            }), 404

        return send_from_directory(Config.UPLOAD_FOLDER, document_name, as_attachment=False)

    def change_password(self):
        data = request.get_json() or {}
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password', '')
        password_error = self._validate_password_change(old_password, new_password, confirm_password)
        if password_error:
            return jsonify({'message': password_error}), 400

        jwt_claims = get_jwt()
        email = jwt_claims.get('email')
        role = jwt_claims.get('role')

        if role == 'admin':
            account = self.admin_repo.find_admin_by_email(email)
            password_table = 'admins'
        elif role == 'librarian':
            account = self.librarian_repo.find_librarian_by_email(email)
            password_table = 'librarians'
        else:
            return jsonify({'message': 'Admin or librarian access required'}), 403

        if not account:
            return jsonify({'message': 'Account not found'}), 404

        if not self.auth_service.verify_password(old_password, account.get('password_hash', '')):
            return jsonify({'message': 'Old password is incorrect'}), 400

        new_hash = self.auth_service.hash_password(new_password)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f'UPDATE {password_table} SET password_hash=%s, updated_at=NOW() WHERE email=%s', (new_hash, email))
                conn.commit()

        return jsonify({'message': 'Password updated successfully'}), 200

    def list_loans(self):
        auth_error = self._require_admin_or_librarian()
        if auth_error:
            return auth_error

        page, limit, offset, paginate = self._parse_pagination_params()
        loan_filter = (request.args.get('status') or 'active').strip().lower()
        if loan_filter not in ['active', 'borrowed', 'overdue', 'returned', 'all']:
            return jsonify({'message': 'Invalid loan status filter'}), 400

        search_query = (request.args.get('search') or '').strip()
        search_terms = []
        if search_query:
            wildcard_search = f"%{search_query}%"
            search_terms = [
                'CAST(br.borrow_id AS CHAR) LIKE %s',
                'CAST(br.student_id AS CHAR) LIKE %s',
                'COALESCE(s.full_name, \'\') LIKE %s',
                'COALESCE(s.student_number, \'\') LIKE %s',
                'COALESCE(s.email, \'\') LIKE %s',
                'COALESCE(b.title, \'\') LIKE %s',
                'COALESCE(b.isbn, \'\') LIKE %s',
                'COALESCE(bc.copy_code, \'\') LIKE %s',
                'COALESCE(bc.barcode_value, \'\') LIKE %s',
                'COALESCE(bc.qr_token, \'\') LIKE %s'
            ]

        where_clauses = []
        if loan_filter == 'active':
            where_clauses.append('br.return_date IS NULL')
        elif loan_filter == 'borrowed':
            where_clauses.append('br.return_date IS NULL')
            where_clauses.append('(br.due_date IS NULL OR DATE(br.due_date) >= CURDATE())')
        elif loan_filter == 'overdue':
            where_clauses.append('br.return_date IS NULL')
            where_clauses.append('br.due_date IS NOT NULL')
            where_clauses.append('DATE(br.due_date) < CURDATE()')
        elif loan_filter == 'returned':
            where_clauses.append('br.return_date IS NOT NULL')

        if search_terms:
            where_clauses.append(f"({' OR '.join(search_terms)})")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ''
        params = tuple([wildcard_search] * len(search_terms)) if search_terms else ()

        with get_connection() as conn:
            ensure_inventory_schema(conn)
            conn.commit()
            with conn.cursor() as cur:
                if paginate:
                    cur.execute(
                        f"SELECT COUNT(*) AS total FROM borrow_records br "
                        f"LEFT JOIN books b ON br.book_id = b.book_id "
                        f"LEFT JOIN book_copies bc ON br.copy_id = bc.copy_id AND bc.book_id = br.book_id "
                        f"LEFT JOIN students s ON br.student_id = s.student_id "
                        f"{where_sql}",
                        params,
                    )
                    total = cur.fetchone().get('total', 0)

                sql = """
                    SELECT
                        br.borrow_id AS loan_id,
                        br.book_id,
                        br.copy_id,
                        bc.copy_code,
                        bc.barcode_value,
                        bc.qr_token,
                        b.title AS book_title,
                        br.student_id,
                        br.student_id AS user_id,
                        s.full_name AS student_name,
                        s.email AS student_email,
                        s.student_number,
                        br.borrow_date AS borrowed_at,
                        br.due_date,
                        br.return_date AS returned_at,
                        CASE
                            WHEN br.return_date IS NOT NULL THEN 'returned'
                            WHEN br.due_date IS NOT NULL AND DATE(br.due_date) < CURDATE() THEN 'overdue'
                            ELSE 'borrowed'
                        END AS status,
                        CASE WHEN br.return_date IS NOT NULL THEN TRUE ELSE FALSE END AS returned,
                        CASE
                            WHEN br.return_date IS NULL
                             AND br.due_date IS NOT NULL
                             AND DATE(br.due_date) < CURDATE()
                            THEN DATEDIFF(CURDATE(), DATE(br.due_date))
                            ELSE 0
                        END AS days_overdue,
                        CASE
                            WHEN br.return_date IS NULL
                             AND br.due_date IS NOT NULL
                             AND DATE(br.due_date) < CURDATE()
                            THEN ROUND(DATEDIFF(CURDATE(), DATE(br.due_date)) * %s, 2)
                            ELSE COALESCE(f.fine_amount, 0)
                        END AS fine_amount
                    FROM borrow_records br
                    LEFT JOIN books b ON br.book_id = b.book_id
                    LEFT JOIN book_copies bc ON br.copy_id = bc.copy_id AND bc.book_id = br.book_id
                    LEFT JOIN students s ON br.student_id = s.student_id
                    LEFT JOIN (
                        SELECT borrow_id, SUM(amount) AS fine_amount
                        FROM fines
                        GROUP BY borrow_id
                    ) f ON br.borrow_id = f.borrow_id
                    """
                if where_sql:
                    sql += f"{where_sql}\n"
                sql += "ORDER BY br.borrow_date DESC"
                if paginate:
                    sql += " LIMIT %s OFFSET %s"
                query_params = [float(getattr(Config, 'FINE_DAILY_RATE', 100.0) or 100.0)]
                query_params.extend(params)
                if paginate:
                    query_params.extend([limit, offset])
                cur.execute(
                    sql,
                    tuple(query_params)
                )
                loans = cur.fetchall()
        if paginate:
            return jsonify({
                'loans': loans,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'total_pages': max(1, (total + limit - 1) // limit)
                }
            }), 200
        return jsonify(loans), 200

    def create_loan(self):
        auth_error = self._require_admin_or_librarian()
        if auth_error:
            return auth_error

        data = request.get_json(silent=True) or {}
        book_id = data.get('book_id')
        student_id = data.get('student_id') or data.get('user_id')
        due_date = data.get('due_date')

        if not book_id or not student_id:
            return jsonify({'message': 'book_id and student_id are required'}), 400

        try:
            book_id = int(book_id)
            student_id = int(student_id)
        except (TypeError, ValueError):
            return jsonify({'message': 'book_id and student_id must be valid integers'}), 400

        if book_id <= 0 or student_id <= 0:
            return jsonify({'message': 'book_id and student_id must be greater than zero'}), 400

        borrowed_at = datetime.utcnow()
        if due_date:
            try:
                due_date = datetime.strptime(str(due_date), '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'message': 'due_date must use YYYY-MM-DD format'}), 400
        else:
            from datetime import timedelta
            due_date = (borrowed_at + timedelta(days=14)).date()

        try:
            loan_id = self.loan_repository.create_loan(book_id, student_id, borrowed_at, due_date)
        except ValueError as exc:
            return jsonify({'message': str(exc)}), 400

        return jsonify({'message': 'Book issued', 'loan_id': loan_id, 'due_date': due_date.isoformat()}), 201

    def list_registration_requests(self):
        auth_error = self._require_admin()
        if auth_error:
            return auth_error

        page, limit, offset, paginate = self._parse_pagination_params()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = DATABASE() "
                    "AND table_name = 'registration_requests' "
                    "AND column_name IN ('status', 'registration_document', 'email_verified', 'verified_at', 'department', 'year_level')"
                )
                existing_columns = {row.get('column_name') for row in cur.fetchall()}

                has_status = 'status' in existing_columns
                has_document = 'registration_document' in existing_columns
                has_email_verified = 'email_verified' in existing_columns
                has_verified_at = 'verified_at' in existing_columns
                has_department = 'department' in existing_columns
                has_year_level = 'year_level' in existing_columns

                select_columns = [
                    'request_id',
                    'email',
                    'full_name',
                    'student_number',
                ]
                if has_document:
                    select_columns.append('registration_document')
                if has_department:
                    select_columns.append('department')
                if has_year_level:
                    select_columns.append('year_level')
                if has_email_verified:
                    select_columns.append('email_verified')
                if has_verified_at:
                    select_columns.append('verified_at')
                select_columns.append('created_at')
                if has_status:
                    select_columns.append('status')

                query = [
                    'SELECT',
                    ', '.join(select_columns),
                    'FROM registration_requests'
                ]

                where_clauses = []
                if has_email_verified:
                    where_clauses.append('email_verified = TRUE')
                if has_status:
                    where_clauses.append("(status IS NULL OR status = 'pending')")

                if where_clauses:
                    query.append('WHERE ' + ' AND '.join(where_clauses))

                count_query = 'SELECT COUNT(*) AS total FROM registration_requests '
                if where_clauses:
                    count_query += 'WHERE ' + ' AND '.join(where_clauses)

                query.append('ORDER BY created_at DESC')
                if paginate:
                    query.append('LIMIT %s OFFSET %s')
                    cur.execute(count_query)
                    total = cur.fetchone().get('total', 0)
                cur.execute(' '.join(query), (limit, offset) if paginate else ())

                requests = cur.fetchall()
                if has_document:
                    for request_row in requests:
                        request_row['document_url'] = url_for(
                            'admin.get_registration_request_document',
                            request_id=request_row['request_id']
                        )

        if paginate:
            return jsonify({
                'requests': requests,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'total_pages': max(1, (total + limit - 1) // limit)
                }
            }), 200

        return jsonify(requests), 200

    def get_registration_request_document(self, request_id):
        auth_error = self._require_admin()
        if auth_error:
            return auth_error

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) AS cnt FROM information_schema.columns "
                    "WHERE table_schema = DATABASE() "
                    "AND table_name = 'registration_requests' "
                    "AND column_name = 'registration_document'"
                )
                document_column = cur.fetchone()
                if not document_column or not document_column.get('cnt'):
                    return jsonify({'message': 'Registration document storage is not enabled'}), 404

                cur.execute(
                    'SELECT registration_document FROM registration_requests WHERE request_id=%s LIMIT 1',
                    (request_id,)
                )
                request_row = cur.fetchone()

        if not request_row:
            return jsonify({'message': 'Registration request not found'}), 404

        document_name = request_row.get('registration_document')
        if not document_name:
            return jsonify({'message': 'No registration document uploaded'}), 404

        file_path = os.path.join(Config.UPLOAD_FOLDER, document_name)
        if not os.path.exists(file_path):
            return jsonify({'message': 'Registration document not found on server'}), 404

        return send_from_directory(Config.UPLOAD_FOLDER, document_name, as_attachment=False)

    def reject_registration(self):
        auth_error = self._require_admin()
        if auth_error:
            return auth_error

        data = request.get_json() or {}
        request_id = data.get('request_id')

        if not request_id:
            return jsonify({'message': 'Request ID is required'}), 400

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT registration_document FROM registration_requests WHERE request_id=%s LIMIT 1',
                    (request_id,)
                )
                request_row = cur.fetchone()
                if not request_row:
                    return jsonify({'message': 'Registration request not found'}), 404

                cur.execute(
                    'DELETE FROM registration_requests WHERE request_id=%s',
                    (request_id,)
                )
                conn.commit()
                updated = cur.rowcount

        if not updated:
            return jsonify({'message': 'Registration request not found'}), 404

        document_name = request_row.get('registration_document') if request_row else None
        if document_name:
            file_path = os.path.join(Config.UPLOAD_FOLDER, document_name)
            if os.path.exists(file_path):
                os.remove(file_path)

        return jsonify({'message': 'Registration request rejected and removed'}), 200
