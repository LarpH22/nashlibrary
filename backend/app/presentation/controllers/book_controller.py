from datetime import datetime, timedelta
from flask import jsonify, request

from ...application.use_cases.book.add_book import AddBookUseCase
from ...application.use_cases.book.borrow_book import BorrowBookUseCase
from ...application.use_cases.book.return_book import ReturnBookUseCase
from ...domain.services.library_service import LibraryService
from ...infrastructure.repositories_impl.book_repository_impl import BookRepositoryImpl
from ...infrastructure.repositories_impl.loan_repository_impl import LoanRepositoryImpl


class BookController:
    def __init__(self):
        self.book_repository = BookRepositoryImpl()
        self.loan_repository = LoanRepositoryImpl()
        self.library_service = LibraryService(self.book_repository, self.loan_repository)
        self.add_book_use_case = AddBookUseCase(self.library_service)
        self.borrow_book_use_case = BorrowBookUseCase(self.library_service)
        self.return_book_use_case = ReturnBookUseCase(self.library_service)

    def list_books(self):
        books = self.book_repository.list_books()
        return jsonify(books), 200

    def add_book(self):
        data = request.get_json() or {}
        title = data.get('title')
        author = data.get('author')
        isbn = data.get('isbn')
        available_copies = data.get('available_copies', 1)
        total_copies = data.get('total_copies', 1)

        if not title or not author or not isbn:
            return jsonify({'message': 'title, author, and isbn are required'}), 400

        book_id = self.add_book_use_case.execute(title, author, isbn, available_copies, total_copies)
        return jsonify({'message': 'Book created', 'book_id': book_id}), 201

    def borrow_book(self, current_user=None):
        if not current_user:
            return jsonify({'message': 'Authentication required'}), 401
        if current_user.get('role') not in ['student', 'admin', 'librarian']:
            return jsonify({'message': 'Library account access required'}), 403

        data = request.get_json() or {}
        book_id = data.get('book_id')
        if current_user.get('role') == 'student':
            user_id = current_user.get('student_id')
        else:
            user_id = data.get('student_id') or data.get('user_id')
        if not book_id:
            return jsonify({'message': 'book_id is required'}), 400
        if not user_id:
            return jsonify({'message': 'Student ID not available for authenticated user'}), 400
        borrowed_at = datetime.utcnow()
        due_date = borrowed_at + timedelta(days=14)
        try:
            loan_id = self.borrow_book_use_case.execute(book_id, user_id, borrowed_at, due_date)
            return jsonify({'message': 'Book borrowed', 'loan_id': loan_id}), 201
        except ValueError as exc:
            return jsonify({'message': str(exc)}), 400

    def return_book(self, current_user=None):
        if not current_user:
            return jsonify({'message': 'Authentication required'}), 401
        if current_user.get('role') not in ['student', 'admin', 'librarian']:
            return jsonify({'message': 'Library account access required'}), 403

        data = request.get_json() or {}
        loan_id = data.get('loan_id')
        if not loan_id:
            return jsonify({'message': 'loan_id is required'}), 400
        student_id = current_user.get('student_id') if current_user.get('role') == 'student' else None
        try:
            returned_loan = self.return_book_use_case.execute(loan_id, datetime.utcnow(), student_id)
            if not returned_loan:
                return jsonify({'message': 'Active loan not found'}), 404
            return jsonify({'message': 'Book returned', 'loan': returned_loan}), 200
        except ValueError as exc:
            return jsonify({'message': str(exc)}), 400
