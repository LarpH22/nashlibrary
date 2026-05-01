from datetime import datetime

from flask import jsonify, request
from flask_jwt_extended import get_jwt

from ...domain.services.auth_service import AuthService
from ...infrastructure.database.db_connection import get_connection
from ...infrastructure.repositories_impl.auth_repository_impl import AdminAuthRepositoryImpl


class AdminController:
    def __init__(self):
        self.admin_repo = AdminAuthRepositoryImpl()
        self.auth_service = AuthService(self.admin_repo, self.admin_repo, self.admin_repo)

    def _require_admin(self):
        jwt_claims = get_jwt()
        if jwt_claims.get('role') != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
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
                cur.execute(
                    'SELECT student_id, email, full_name, student_number, department, year_level, status FROM students WHERE student_id=%s LIMIT 1',
                    (student_id,)
                )
                student = cur.fetchone()
                if not student:
                    return jsonify({'message': 'Student not found'}), 404

                cur.execute(
                    'SELECT loan_id, book_id, user_id, borrowed_at, due_date, returned_at, status FROM borrow_records WHERE user_id=%s ORDER BY borrowed_at DESC',
                    (student_id,)
                )
                loans = cur.fetchall()

        student['loans'] = loans
        return jsonify(student), 200

    def change_password(self):
        auth_error = self._require_admin()
        if auth_error:
            return auth_error

        data = request.get_json() or {}
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        if not old_password or not new_password:
            return jsonify({'message': 'Old and new passwords are required'}), 400

        jwt_claims = get_jwt()
        email = jwt_claims.get('email')
        admin = self.admin_repo.find_admin_by_email(email)
        if not admin:
            return jsonify({'message': 'Admin account not found'}), 404

        if not self.auth_service.verify_password(old_password, admin.get('password_hash', '')):
            return jsonify({'message': 'Old password is incorrect'}), 401

        new_hash = self.auth_service.hash_password(new_password)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE admins SET password_hash=%s, updated_at=NOW() WHERE email=%s', (new_hash, email))
                conn.commit()

        return jsonify({'message': 'Password updated successfully'}), 200

    def list_loans(self):
        auth_error = self._require_admin()
        if auth_error:
            return auth_error

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    SELECT
                        br.borrow_id AS loan_id,
                        br.book_id,
                        b.title AS book_title,
                        br.student_id,
                        s.full_name AS student_name,
                        br.borrow_date AS borrowed_at,
                        br.due_date,
                        br.return_date AS returned_at,
                        br.status
                    FROM borrow_records br
                    LEFT JOIN books b ON br.book_id = b.book_id
                    LEFT JOIN students s ON br.student_id = s.student_id
                    ORDER BY br.borrow_date DESC
                    '''
                )
                loans = cur.fetchall()
        return jsonify(loans), 200
