from datetime import datetime
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
        if current_user.get('role') != 'student':
            return jsonify({'message': 'Students can only request books. Librarians approve requests.'}), 403

        data = request.get_json() or {}
        book_id = data.get('book_id')
        user_id = current_user.get('student_id')
        if not book_id:
            return jsonify({'message': 'book_id is required'}), 400
        if not user_id:
            return jsonify({'message': 'Student ID not available for authenticated user'}), 400

        try:
            request_id = self.loan_repository.create_borrow_request(int(book_id), int(user_id))
            return jsonify({'message': 'Borrow request submitted', 'request_id': request_id, 'status': 'pending'}), 201
        except ValueError as exc:
            return jsonify({'message': str(exc)}), 400
        except (TypeError, ValueError):
            return jsonify({'message': 'book_id must be a valid integer'}), 400

    def list_borrow_requests(self, current_user=None):
        if not current_user:
            return jsonify({'message': 'Authentication required'}), 401
        if current_user.get('role') not in ['admin', 'librarian']:
            return jsonify({'message': 'Librarian or admin access required'}), 403

        status = request.args.get('status', '').strip().lower() or None
        if status and status not in ['pending', 'approved', 'rejected']:
            return jsonify({'message': 'Invalid request status'}), 400

        requests = self.loan_repository.list_borrow_requests(status)
        return jsonify(requests), 200

    def approve_borrow_request(self, request_id: int, current_user=None):
        if not current_user:
            return jsonify({'message': 'Authentication required'}), 401
        if current_user.get('role') not in ['admin', 'librarian']:
            return jsonify({'message': 'Librarian or admin access required'}), 403

        data = request.get_json() or {}
        due_date = data.get('due_date')
        if not due_date:
            return jsonify({'message': 'due_date is required before approval'}), 400

        try:
            borrow_id = self.loan_repository.approve_borrow_request(
                int(request_id),
                due_date,
                current_user.get('librarian_id') or current_user.get('admin_id') or current_user.get('user_id'),
            )
        except ValueError as exc:
            return jsonify({'message': str(exc)}), 400

        if not borrow_id:
            return jsonify({'message': 'Pending borrow request not found'}), 404

        return jsonify({'message': 'Borrow request approved', 'loan_id': borrow_id}), 200

    def reject_borrow_request(self, request_id: int, current_user=None):
        if not current_user:
            return jsonify({'message': 'Authentication required'}), 401
        if current_user.get('role') not in ['admin', 'librarian']:
            return jsonify({'message': 'Librarian or admin access required'}), 403

        data = request.get_json() or {}
        rejected = self.loan_repository.reject_borrow_request(int(request_id), data.get('reason'))
        if not rejected:
            return jsonify({'message': 'Pending borrow request not found'}), 404

        return jsonify({'message': 'Borrow request rejected'}), 200

    def return_book(self, current_user=None):
        if not current_user:
            return jsonify({'message': 'Authentication required'}), 401
        if current_user.get('role') not in ['student', 'admin', 'librarian']:
            return jsonify({'message': 'Library account access required'}), 403

        data = request.get_json() or {}
        loan_id = data.get('loan_id')
        if loan_id is None:
            return jsonify({'message': 'loan_id is required'}), 400

        try:
            loan_id = int(loan_id)
        except (TypeError, ValueError):
            return jsonify({'message': 'loan_id must be a valid integer'}), 400

        if loan_id <= 0:
            return jsonify({'message': 'loan_id must be greater than zero'}), 400

        try:
            student_id = current_user.get('student_id') if current_user.get('role') == 'student' else None
            returned_loan = self.return_book_use_case.execute(loan_id, datetime.utcnow(), student_id)
        except ValueError as exc:
            return jsonify({'message': str(exc)}), 400

        if not returned_loan:
            return jsonify({'message': 'Active loan not found'}), 404

        return jsonify({'message': 'Book returned', 'loan': returned_loan}), 200
