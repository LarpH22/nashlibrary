from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from ..controllers.book_controller import BookController
from ...infrastructure.database.db_connection import get_connection

api_bp = Blueprint('api', __name__)
book_controller = BookController()


def _require_librarian_or_admin():
    jwt_claims = get_jwt()
    if jwt_claims.get('role') not in ['librarian', 'admin']:
        return jsonify({'message': 'Librarian or admin access required'}), 403
    return None


@api_bp.route('/books', methods=['GET'])
def list_books():
    return book_controller.list_books()


@api_bp.route('/loans', methods=['GET'])
@jwt_required()
def list_loans():
    auth_error = _require_librarian_or_admin()
    if auth_error:
        return auth_error

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT loan_id, book_id, user_id, borrowed_at, due_date, returned_at, status
                FROM borrow_records
                ORDER BY borrowed_at DESC
                '''
            )
            loans = cur.fetchall()
    return jsonify(loans), 200


@api_bp.route('/students', methods=['GET'])
@jwt_required()
def list_students():
    auth_error = _require_librarian_or_admin()
    if auth_error:
        return auth_error

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT student_id, email, full_name, student_number, department, year_level, status
                FROM students
                ORDER BY full_name ASC
                '''
            )
            students = cur.fetchall()
    return jsonify(students), 200


@api_bp.route('/loans/issue', methods=['POST'])
@jwt_required()
def issue_loan():
    auth_error = _require_librarian_or_admin()
    if auth_error:
        return auth_error
    return book_controller.borrow_book()


@api_bp.route('/loans/<int:loan_id>/return', methods=['POST'])
@jwt_required()
def return_loan(loan_id):
    auth_error = _require_librarian_or_admin()
    if auth_error:
        return auth_error

    try:
        returned_loan = book_controller.return_book_use_case.execute(loan_id, datetime.utcnow())
    except ValueError as exc:
        return jsonify({'message': str(exc)}), 400

    return jsonify({'message': 'Book returned', 'loan': returned_loan}), 200


def _require_student():
    jwt_claims = get_jwt()
    if jwt_claims.get('role') != 'student':
        return jsonify({'message': 'Student access required'}), 403
    return None


@api_bp.route('/loans/student', methods=['GET'])
@jwt_required()
def list_student_loans():
    auth_error = _require_student()
    if auth_error:
        return auth_error

    jwt_claims = get_jwt()
    student_id = jwt_claims.get('student_id')

    if not student_id:
        email = get_jwt_identity()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT student_id FROM students WHERE email=%s LIMIT 1', (email,))
                student = cur.fetchone()
                student_id = student.get('student_id') if student else None

    if not student_id:
        return jsonify({'message': 'Student record not found'}), 404

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT
                    br.borrow_id AS loan_id,
                    br.book_id,
                    b.title AS book_title,
                    br.borrow_date AS issue_date,
                    br.due_date,
                    br.return_date AS return_date,
                    br.status,
                    CASE WHEN br.status='returned' THEN TRUE ELSE FALSE END AS returned
                FROM borrow_records br
                LEFT JOIN books b ON br.book_id = b.book_id
                WHERE br.student_id=%s
                ORDER BY br.borrow_date DESC
                ''',
                (student_id,)
            )
            loans = cur.fetchall()

            for loan in loans:
                due_date = loan.get('due_date')
                return_date = loan.get('return_date')
                effective_date = return_date or datetime.utcnow().date()
                days_overdue = 0
                fine_amount = 0.0

                if due_date:
                    if isinstance(effective_date, datetime):
                        effective_date = effective_date.date()
                    if isinstance(due_date, datetime):
                        due_date = due_date.date()
                    if effective_date > due_date:
                        days_overdue = (effective_date - due_date).days
                        fine_amount = round(days_overdue * 1.0, 2)

                loan['days_overdue'] = days_overdue
                loan['fine_amount'] = fine_amount

                for field in ['issue_date', 'due_date', 'return_date']:
                    if field in loan and loan[field] is not None:
                        value = loan[field]
                        if hasattr(value, 'isoformat'):
                            loan[field] = value.isoformat()

    return jsonify(loans), 200


@api_bp.route('/students/profile', methods=['GET'])
@jwt_required()
def get_student_profile():
    auth_error = _require_student()
    if auth_error:
        return auth_error

    jwt_claims = get_jwt()
    email = jwt_claims.get('email')
    if not email:
        return jsonify({'message': 'Invalid token claims'}), 401

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT student_id, email, full_name, student_number, department,
                       year_level, phone, status, email_verified, created_at
                FROM students
                WHERE email=%s
                LIMIT 1
                ''',
                (email,)
            )
            student = cur.fetchone()

    if not student:
        return jsonify({'message': 'Student not found'}), 404

    return jsonify(student), 200


@api_bp.route('/students/profile', methods=['PUT'])
@jwt_required()
def update_student_profile():
    auth_error = _require_student()
    if auth_error:
        return auth_error

    jwt_claims = get_jwt()
    current_email = jwt_claims.get('email')
    data = request.get_json() or {}
    full_name = data.get('full_name')
    new_email = data.get('email') or current_email
    phone = data.get('phone')

    if not full_name:
        return jsonify({'message': 'Full name is required.'}), 400

    with get_connection() as conn:
        with conn.cursor() as cur:
            if new_email != current_email:
                cur.execute('SELECT 1 FROM students WHERE email=%s AND email != %s LIMIT 1', (new_email, current_email))
                if cur.fetchone():
                    return jsonify({'message': 'Email is already in use.'}), 400

            cur.execute(
                '''
                UPDATE students
                SET full_name=%s, email=%s, phone=%s, updated_at=NOW()
                WHERE email=%s
                ''',
                (full_name, new_email, phone, current_email)
            )
            conn.commit()
            if cur.rowcount == 0:
                return jsonify({'message': 'Student not found'}), 404

            cur.execute(
                '''
                SELECT student_id, email, full_name, student_number, department,
                       year_level, phone, status, email_verified, created_at
                FROM students
                WHERE email=%s
                LIMIT 1
                ''',
                (new_email,)
            )
            student = cur.fetchone()

    return jsonify(student), 200
