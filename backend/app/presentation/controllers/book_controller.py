import os
import socket
import uuid
from datetime import datetime, timedelta
from html import escape
from urllib.parse import quote

from flask import Response, jsonify, make_response, request, send_file, redirect, current_app
from werkzeug.utils import secure_filename

from ...application.use_cases.book.add_book import AddBookUseCase
from ...application.use_cases.book.borrow_book import BorrowBookUseCase
from ...application.use_cases.book.return_book import ReturnBookUseCase
from ...domain.services.library_service import LibraryService
from ...infrastructure.config import Config
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
        for book in books:
            book['detail_url'] = f"/books/{book['book_id']}"
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
        base_url = self._frontend_base_url(data)
        return jsonify({
            'message': 'Book created',
            'book_id': book_id,
            'detail_url': f"{base_url}/books/{book_id}",
        }), 201

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

    def list_book_copies(self, current_user=None):
        if not current_user or current_user.get('role') not in ['admin', 'librarian']:
            return jsonify({'message': 'Admin or librarian access required'}), 403

        book_id = request.args.get('book_id', type=int)
        return jsonify({'copies': self.book_repository.list_copies(book_id)}), 200

    def lookup_copy_by_scan(self, current_user=None):
        if not current_user or current_user.get('role') not in ['student', 'admin', 'librarian']:
            return jsonify({'message': 'Library account access required'}), 403

        scan_code = (request.args.get('code') or '').strip()
        if not scan_code:
            data = request.get_json(silent=True) or {}
            scan_code = str(data.get('code') or '').strip()
        if not scan_code:
            return jsonify({'message': 'Barcode is required'}), 400

        copy = self.book_repository.find_copy_by_scan_code(scan_code)
        if not copy:
            return jsonify({'message': 'Book copy not found'}), 404
        copy['detail_url'] = f"{Config.FRONTEND_URL.rstrip('/')}/dashboard?copy={quote(copy['barcode_value'] or copy['copy_code'])}"
        return jsonify({'copy': copy}), 200

    def borrow_by_scan(self, current_user=None):
        if not current_user:
            return jsonify({'message': 'Authentication required'}), 401
        if current_user.get('role') not in ['student', 'admin', 'librarian']:
            return jsonify({'message': 'Library account access required'}), 403

        data = request.get_json() or {}
        scan_code = str(data.get('code') or data.get('barcode') or '').strip()
        if not scan_code:
            return jsonify({'message': 'Barcode is required'}), 400

        copy = self.book_repository.find_copy_by_scan_code(scan_code)
        if not copy:
            return jsonify({'message': 'Book copy not found'}), 404

        if current_user.get('role') == 'student':
            user_id = current_user.get('student_id')
        else:
            user_id = data.get('student_id') or data.get('user_id')
        if not user_id:
            return jsonify({'message': 'Student ID is required'}), 400

        borrowed_at = datetime.utcnow()
        due_date = borrowed_at + timedelta(days=14)
        try:
            loan_id = self.loan_repository.create_loan_for_copy(copy['copy_id'], int(user_id), borrowed_at, due_date)
            return jsonify({'message': 'Book issued from scan', 'loan_id': loan_id, 'copy': copy}), 201
        except (TypeError, ValueError) as exc:
            return jsonify({'message': str(exc)}), 400

    def return_by_scan(self, current_user=None):
        if not current_user:
            return jsonify({'message': 'Authentication required'}), 401
        if current_user.get('role') not in ['student', 'admin', 'librarian']:
            return jsonify({'message': 'Library account access required'}), 403

        data = request.get_json() or {}
        scan_code = str(data.get('code') or data.get('barcode') or '').strip()
        if not scan_code:
            return jsonify({'message': 'Barcode is required'}), 400

        student_id = current_user.get('student_id') if current_user.get('role') == 'student' else None
        try:
            returned_loan = self.loan_repository.close_loan_by_copy_code(scan_code, datetime.utcnow(), student_id)
        except ValueError as exc:
            return jsonify({'message': str(exc)}), 400

        if not returned_loan:
            return jsonify({'message': 'Active loan not found for scanned copy'}), 404
        return jsonify({'message': 'Book returned from scan', 'loan': returned_loan}), 200

    def book_detail(self, book_id):
        if request.accept_mimetypes['text/html'] >= request.accept_mimetypes['application/json']:
            return redirect(f"/books/{book_id}", code=302)

        book = self.book_repository.find_by_id(book_id)
        if not book:
            return jsonify({'message': 'Book not found'}), 404

        ebooks = self.book_repository.list_ebooks(book_id)
        for ebook in ebooks:
            ebook['detail_url'] = f"/ebooks/{ebook['ebook_id']}"
            ebook['access_url'] = f"/books/ebooks/{ebook['ebook_id']}/public-download"

        book['detail_url'] = f"/books/{book['book_id']}"
        book['ebooks'] = ebooks
        return jsonify({'book': book}), 200

    def upload_ebook(self, current_user=None):
        if not current_user or current_user.get('role') not in ['admin', 'librarian']:
            return jsonify({'message': 'Admin or librarian access required'}), 403

        book_id = request.form.get('book_id', type=int)
        title = (request.form.get('title') or '').strip()
        file = request.files.get('ebook')
        if not book_id:
            return jsonify({'message': 'book_id is required'}), 400
        if not file or not file.filename:
            return jsonify({'message': 'PDF or EPUB file is required'}), 400

        safe_name = secure_filename(file.filename)
        extension = safe_name.rsplit('.', 1)[-1].lower() if '.' in safe_name else ''
        if extension not in Config.ALLOWED_EBOOK_EXTENSIONS:
            return jsonify({'message': 'Only PDF and EPUB e-books are allowed'}), 400

        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size <= 0:
            return jsonify({'message': 'Uploaded e-book is empty'}), 400
        if file_size > Config.MAX_CONTENT_LENGTH:
            return jsonify({'message': 'Uploaded e-book exceeds the configured maximum file size'}), 400

        os.makedirs(Config.EBOOK_UPLOAD_FOLDER, exist_ok=True)
        stored_filename = f"{uuid.uuid4().hex}.{extension}"
        file_path = os.path.join(Config.EBOOK_UPLOAD_FOLDER, stored_filename)
        file.save(file_path)

        uploaded_by_id = current_user.get('admin_id') or current_user.get('librarian_id')
        try:
            ebook_id = self.book_repository.create_ebook(
                book_id=book_id,
                title=title or safe_name.rsplit('.', 1)[0],
                original_filename=safe_name,
                stored_filename=stored_filename,
                file_path=file_path,
                file_type=extension,
                file_size=file_size,
                uploaded_by_role=current_user.get('role'),
                uploaded_by_id=uploaded_by_id,
            )
        except ValueError as exc:
            try:
                os.remove(file_path)
            except OSError:
                pass
            return jsonify({'message': str(exc)}), 404

        base_url = self._frontend_base_url()
        return jsonify({
            'message': 'E-book uploaded',
            'ebook_id': ebook_id,
            'detail_url': f"{base_url}/ebooks/{ebook_id}",
        }), 201

    def list_ebooks(self, current_user=None):
        if not current_user or current_user.get('role') not in ['student', 'admin', 'librarian']:
            return jsonify({'message': 'Library account access required'}), 403
        book_id = request.args.get('book_id', type=int)
        ebooks = self.book_repository.list_ebooks(book_id)
        for ebook in ebooks:
            ebook['access_url'] = f"/books/ebooks/{ebook['ebook_id']}/download"
            ebook['detail_url'] = f"/ebooks/{ebook['ebook_id']}"
        return jsonify({'ebooks': ebooks}), 200

    def download_ebook(self, ebook_id, current_user=None):
        if not current_user or current_user.get('role') not in ['student', 'admin', 'librarian']:
            return jsonify({'message': 'Library account access required'}), 403

        ebook = self.book_repository.find_ebook(ebook_id)
        if not ebook:
            return jsonify({'message': 'E-book not found'}), 404

        file_path = os.path.abspath(ebook['file_path'])
        upload_root = os.path.abspath(Config.EBOOK_UPLOAD_FOLDER)
        if os.path.commonpath([upload_root, file_path]) != upload_root or not os.path.exists(file_path):
            return jsonify({'message': 'E-book file is not available'}), 404

        actor_id = current_user.get('student_id') or current_user.get('librarian_id') or current_user.get('admin_id')
        self.book_repository.log_ebook_access(ebook_id, current_user.get('role'), actor_id, 'download')
        return send_file(
            file_path,
            as_attachment=request.args.get('disposition') != 'inline',
            download_name=ebook['original_filename'],
            mimetype='application/pdf' if ebook['file_type'] == 'pdf' else 'application/epub+zip',
            conditional=True,
        )

    def ebook_detail(self, ebook_id):
        ebook = self.book_repository.find_ebook(ebook_id)
        if not ebook:
            return jsonify({'message': 'E-book not found'}), 404

        book = self.book_repository.find_by_id(ebook['book_id'])
        ebook['detail_url'] = f"/ebooks/{ebook['ebook_id']}"
        ebook['access_url'] = f"/books/ebooks/{ebook['ebook_id']}/public-download"
        if book:
            book['detail_url'] = f"/books/{book['book_id']}"
        self.book_repository.log_ebook_access(ebook_id, 'student', None, 'view')
        return jsonify({'ebook': ebook, 'book': book}), 200

    def public_download_ebook(self, ebook_id):
        ebook = self.book_repository.find_ebook(ebook_id)
        if not ebook:
            return jsonify({'message': 'E-book not found'}), 404

        file_path = os.path.abspath(ebook['file_path'])
        upload_root = os.path.abspath(Config.EBOOK_UPLOAD_FOLDER)
        if os.path.commonpath([upload_root, file_path]) != upload_root or not os.path.exists(file_path):
            return jsonify({'message': 'E-book file is not available'}), 404

        self.book_repository.log_ebook_access(ebook_id, 'student', None, 'download')
        return send_file(
            file_path,
            as_attachment=True,
            download_name=ebook['original_filename'],
            mimetype='application/pdf' if ebook['file_type'] == 'pdf' else 'application/epub+zip',
            conditional=True,
        )

    def delete_ebook(self, ebook_id, current_user=None):
        if not current_user or current_user.get('role') not in ['admin', 'librarian']:
            return jsonify({'message': 'Admin or librarian access required'}), 403

        ebook = self.book_repository.find_ebook(ebook_id)
        if not ebook:
            return jsonify({'message': 'E-book not found'}), 404

        blockers = self.book_repository.get_ebook_delete_blockers(ebook_id)
        if blockers is None:
            return jsonify({'message': 'E-book not found'}), 404
        if blockers:
            return jsonify({
                'message': 'E-book cannot be deleted while it is borrowed, being accessed, or referenced.',
                'blockers': blockers,
            }), 409

        deleted_ebook = self.book_repository.delete_ebook(ebook_id)
        if not deleted_ebook:
            return jsonify({'message': 'E-book not found'}), 404

        file_path = os.path.abspath(deleted_ebook['file_path'])
        upload_root = os.path.abspath(Config.EBOOK_UPLOAD_FOLDER)
        if os.path.commonpath([upload_root, file_path]) == upload_root and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as exc:
                return jsonify({
                    'message': 'E-book database record was deleted, but the stored file could not be removed.',
                    'detail': str(exc),
                }), 500

        return jsonify({'message': 'E-book deleted'}), 200

    def _frontend_base_url(self, data=None):
        data = data or {}
        explicit_base_url = (data.get('base_url') or request.args.get('base_url') or '').strip()
        if explicit_base_url:
            return explicit_base_url.rstrip('/')
        return request.host_url.rstrip('/')
