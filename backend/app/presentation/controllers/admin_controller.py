import os
from datetime import datetime

from flask import jsonify, request, send_from_directory, url_for
from flask_jwt_extended import get_jwt

from ...domain.services.auth_service import AuthService
from ...infrastructure.config import Config
from ...infrastructure.database.db_connection import get_connection
from ...infrastructure.repositories_impl.inventory_schema import ensure_inventory_schema
from ...infrastructure.repositories_impl.auth_repository_impl import AdminAuthRepositoryImpl, LibrarianAuthRepositoryImpl


class AdminController:
    def __init__(self):
        self.admin_repo = AdminAuthRepositoryImpl()
        self.librarian_repo = LibrarianAuthRepositoryImpl()
        self.auth_service = AuthService(self.admin_repo, self.librarian_repo, self.admin_repo)

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

    def list_categories(self):
        auth_error = self._require_admin()
        if auth_error:
            return auth_error

        with get_connection() as conn:
            with conn.cursor() as cur:
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

        with get_connection() as conn:
            with conn.cursor() as cur:
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
        auth_error = self._require_admin()
        if auth_error:
            return auth_error

        with get_connection() as conn:
            with conn.cursor() as cur:
                if str(student_id).isdigit():
                    cur.execute(
                        'SELECT student_id, email, full_name, student_number, department, year_level, status FROM students WHERE student_id=%s OR student_number=%s LIMIT 1',
                        (int(student_id), student_id)
                    )
                else:
                    cur.execute(
                        'SELECT student_id, email, full_name, student_number, department, year_level, status FROM students WHERE student_number=%s LIMIT 1',
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

        student['loans'] = loans
        return jsonify(student), 200

    def list_students(self):
        auth_error = self._require_admin_or_librarian()
        if auth_error:
            return auth_error

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT student_id AS user_id, email, full_name, status FROM students ORDER BY full_name ASC')
                students = cur.fetchall()

        return jsonify(students), 200

    def change_password(self):
        data = request.get_json() or {}
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        if not old_password or not new_password:
            return jsonify({'message': 'Old and new passwords are required'}), 400

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

        with get_connection() as conn:
            ensure_inventory_schema(conn)
            conn.commit()
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    SELECT
                        br.borrow_id AS loan_id,
                        br.book_id,
                        br.copy_id,
                        bc.copy_code,
                        b.title AS book_title,
                        br.student_id,
                        s.full_name AS student_name,
                        br.borrow_date AS borrowed_at,
                        br.due_date,
                        br.return_date AS returned_at,
                        br.status
                    FROM borrow_records br
                    LEFT JOIN books b ON br.book_id = b.book_id
                    LEFT JOIN book_copies bc ON br.copy_id = bc.copy_id
                    LEFT JOIN students s ON br.student_id = s.student_id
                    ORDER BY br.borrow_date DESC
                    '''
                )
                loans = cur.fetchall()
        return jsonify(loans), 200

    def list_registration_requests(self):
        auth_error = self._require_admin()
        if auth_error:
            return auth_error

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

                query.append('ORDER BY created_at DESC')
                cur.execute(' '.join(query))

                requests = cur.fetchall()
                if has_document:
                    for request_row in requests:
                        request_row['document_url'] = url_for(
                            'admin.get_registration_request_document',
                            request_id=request_row['request_id']
                        )

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
                    'UPDATE registration_requests SET status=%s WHERE request_id=%s',
                    ('rejected', request_id)
                )
                conn.commit()
                updated = cur.rowcount

        if not updated:
            return jsonify({'message': 'Registration request not found'}), 404

        return jsonify({'message': 'Registration request rejected'}), 200
