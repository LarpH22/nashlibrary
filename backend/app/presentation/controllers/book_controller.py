import os
import uuid
from datetime import datetime, timedelta
from html import escape
from urllib.parse import quote

from flask import Response, jsonify, request, send_file
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
            book['qr_url'] = book.get('qr_code_path') and self._public_upload_url(book['qr_code_path'])
            if not book['qr_url']:
                book['qr_url'] = f"/books/{book['book_id']}/qr.png"
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
        qr_code_path = self._generate_book_qr_code(book_id, base_url)
        return jsonify({
            'message': 'Book created',
            'book_id': book_id,
            'detail_url': f"{base_url}/books/{book_id}",
            'qr_code_path': qr_code_path,
            'qr_code_url': self._public_upload_url(qr_code_path),
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
            return jsonify({'message': 'Barcode or QR code is required'}), 400

        copy = self.book_repository.find_copy_by_scan_code(scan_code)
        if not copy:
            return jsonify({'message': 'Book copy not found'}), 404
        copy['detail_url'] = f"{Config.FRONTEND_URL.rstrip('/')}/dashboard?copy={quote(copy['qr_token'] or copy['barcode_value'] or copy['copy_code'])}"
        return jsonify({'copy': copy}), 200

    def borrow_by_scan(self, current_user=None):
        if not current_user:
            return jsonify({'message': 'Authentication required'}), 401
        if current_user.get('role') not in ['student', 'admin', 'librarian']:
            return jsonify({'message': 'Library account access required'}), 403

        data = request.get_json() or {}
        scan_code = str(data.get('code') or data.get('barcode') or data.get('qr_token') or '').strip()
        if not scan_code:
            return jsonify({'message': 'Barcode or QR code is required'}), 400

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
        scan_code = str(data.get('code') or data.get('barcode') or data.get('qr_token') or '').strip()
        if not scan_code:
            return jsonify({'message': 'Barcode or QR code is required'}), 400

        student_id = current_user.get('student_id') if current_user.get('role') == 'student' else None
        try:
            returned_loan = self.loan_repository.close_loan_by_copy_code(scan_code, datetime.utcnow(), student_id)
        except ValueError as exc:
            return jsonify({'message': str(exc)}), 400

        if not returned_loan:
            return jsonify({'message': 'Active loan not found for scanned copy'}), 404
        return jsonify({'message': 'Book returned from scan', 'loan': returned_loan}), 200

    def copy_qr_svg(self, copy_id):
        copies = self.book_repository.list_copies()
        copy = next((row for row in copies if int(row['copy_id']) == int(copy_id)), None)
        if not copy:
            return jsonify({'message': 'Book copy not found'}), 404

        token = copy.get('qr_token') or copy.get('barcode_value') or copy.get('copy_code')
        target_url = f"{Config.FRONTEND_URL.rstrip('/')}/books/{copy['book_id']}?copy={quote(token)}"
        qr_svg = self._qrcode_svg(target_url)
        if qr_svg:
            return Response(qr_svg, mimetype='image/svg+xml')
        svg = self._deterministic_qr_svg(target_url, copy.get('copy_code') or token)
        return Response(svg, mimetype='image/svg+xml')

    def book_detail(self, book_id):
        book = self.book_repository.find_by_id(book_id)
        if not book:
            return jsonify({'message': 'Book not found'}), 404

        ebooks = self.book_repository.list_ebooks(book_id)
        for ebook in ebooks:
            ebook['detail_url'] = f"/ebooks/{ebook['ebook_id']}"
            ebook['access_url'] = f"/books/ebooks/{ebook['ebook_id']}/public-download"
            ebook['qr_url'] = ebook.get('qr_code_path') and self._public_upload_url(ebook['qr_code_path'])
            if not ebook['qr_url']:
                ebook['qr_url'] = f"/books/ebooks/{ebook['ebook_id']}/qr.png"

        book['detail_url'] = f"/books/{book['book_id']}"
        book['qr_url'] = book.get('qr_code_path') and self._public_upload_url(book['qr_code_path'])
        if not book['qr_url']:
            book['qr_url'] = f"/books/{book['book_id']}/qr.png"
        book['ebooks'] = ebooks
        return jsonify({'book': book}), 200

    def book_qr_svg(self, book_id):
        book = self.book_repository.find_by_id(book_id)
        if not book:
            return jsonify({'message': 'Book not found'}), 404

        target_url = f"{self._frontend_base_url()}/books/{book_id}"
        qr_svg = self._qrcode_svg(target_url)
        if not qr_svg:
            return jsonify({'message': 'QR code generation is unavailable'}), 500
        return Response(qr_svg, mimetype='image/svg+xml')

    def book_qr_png(self, book_id):
        book = self.book_repository.find_by_id(book_id)
        if not book:
            return jsonify({'message': 'Book not found'}), 404

        base_url = self._frontend_base_url()
        qr_code_path = book.get('qr_code_path')
        if not qr_code_path or not self._stored_qr_exists(qr_code_path):
            qr_code_path = self._generate_book_qr_code(book_id, base_url)

        file_path = self._absolute_upload_path(qr_code_path)
        return send_file(file_path, mimetype='image/png', conditional=True)

    def bulk_generate_book_qr_codes(self, current_user=None):
        if not current_user or current_user.get('role') not in ['admin', 'librarian']:
            return jsonify({'message': 'Admin or librarian access required'}), 403

        data = request.get_json(silent=True) or {}
        base_url = self._frontend_base_url(data)
        force = bool(data.get('force') or request.args.get('force') in ['1', 'true', 'yes'])
        include_ebooks = data.get('include_ebooks', True)
        books = self.book_repository.list_books() if force else self.book_repository.list_books_missing_qr()
        ebooks = self.book_repository.list_ebooks() if force else self.book_repository.list_ebooks_missing_qr()

        generated_books = []
        generated_ebooks = []
        failed = []
        for book in books:
            try:
                qr_code_path = self._generate_book_qr_code(book['book_id'], base_url)
                generated_books.append({
                    'book_id': book['book_id'],
                    'qr_code_path': qr_code_path,
                    'qr_code_url': self._public_upload_url(qr_code_path),
                    'detail_url': f"{base_url}/books/{book['book_id']}",
                })
            except Exception as exc:
                failed.append({'book_id': book.get('book_id'), 'message': str(exc)})

        if include_ebooks:
            for ebook in ebooks:
                try:
                    qr_code_path = self._generate_ebook_qr_code(ebook['ebook_id'], base_url)
                    generated_ebooks.append({
                        'ebook_id': ebook['ebook_id'],
                        'qr_code_path': qr_code_path,
                        'qr_code_url': self._public_upload_url(qr_code_path),
                        'detail_url': f"{base_url}/ebooks/{ebook['ebook_id']}",
                    })
                except Exception as exc:
                    failed.append({'ebook_id': ebook.get('ebook_id'), 'message': str(exc)})

        return jsonify({
            'message': 'Book QR code generation complete',
            'base_url': base_url,
            'generated_count': len(generated_books) + len(generated_ebooks),
            'generated_book_count': len(generated_books),
            'generated_ebook_count': len(generated_ebooks),
            'failed_count': len(failed),
            'generated_books': generated_books,
            'generated_ebooks': generated_ebooks,
            'failed': failed,
        }), 200 if not failed else 207

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
        qr_code_path = self._generate_ebook_qr_code(ebook_id, base_url)
        return jsonify({
            'message': 'E-book uploaded',
            'ebook_id': ebook_id,
            'detail_url': f"{base_url}/ebooks/{ebook_id}",
            'qr_code_path': qr_code_path,
            'qr_code_url': self._public_upload_url(qr_code_path),
        }), 201

    def list_ebooks(self, current_user=None):
        if not current_user or current_user.get('role') not in ['student', 'admin', 'librarian']:
            return jsonify({'message': 'Library account access required'}), 403
        book_id = request.args.get('book_id', type=int)
        ebooks = self.book_repository.list_ebooks(book_id)
        for ebook in ebooks:
            ebook['access_url'] = f"/books/ebooks/{ebook['ebook_id']}/download"
            ebook['detail_url'] = f"/ebooks/{ebook['ebook_id']}"
            ebook['qr_url'] = ebook.get('qr_code_path') and self._public_upload_url(ebook['qr_code_path'])
            if not ebook['qr_url']:
                ebook['qr_url'] = f"/books/ebooks/{ebook['ebook_id']}/qr.png"
            ebook['file_available'] = bool(self._resolve_ebook_file_path(ebook))
        return jsonify({'ebooks': ebooks}), 200

    def download_ebook(self, ebook_id, current_user=None):
        if not current_user or current_user.get('role') not in ['student', 'admin', 'librarian']:
            return jsonify({'message': 'Library account access required'}), 403

        ebook = self.book_repository.find_ebook(ebook_id)
        if not ebook:
            return jsonify({'message': 'E-book not found'}), 404

        file_path = self._resolve_ebook_file_path(ebook)
        if not file_path:
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
        ebook['qr_url'] = ebook.get('qr_code_path') and self._public_upload_url(ebook['qr_code_path'])
        if not ebook['qr_url']:
            ebook['qr_url'] = f"/books/ebooks/{ebook['ebook_id']}/qr.png"
        if book:
            book['detail_url'] = f"/books/{book['book_id']}"
            book['qr_url'] = book.get('qr_code_path') and self._public_upload_url(book['qr_code_path'])
            if not book['qr_url']:
                book['qr_url'] = f"/books/{book['book_id']}/qr.svg"
        self.book_repository.log_ebook_access(ebook_id, 'student', None, 'view')
        return jsonify({'ebook': ebook, 'book': book}), 200

    def ebook_qr_svg(self, ebook_id):
        ebook = self.book_repository.find_ebook(ebook_id)
        if not ebook:
            return jsonify({'message': 'E-book not found'}), 404

        target_url = f"{self._frontend_base_url()}/ebooks/{ebook_id}"
        qr_svg = self._qrcode_svg(target_url)
        if not qr_svg:
            return jsonify({'message': 'QR code generation is unavailable'}), 500
        return Response(qr_svg, mimetype='image/svg+xml')

    def ebook_qr_png(self, ebook_id):
        ebook = self.book_repository.find_ebook(ebook_id)
        if not ebook:
            return jsonify({'message': 'E-book not found'}), 404

        base_url = self._frontend_base_url()
        qr_code_path = ebook.get('qr_code_path')
        if not qr_code_path or not self._stored_qr_exists(qr_code_path):
            qr_code_path = self._generate_ebook_qr_code(ebook_id, base_url)

        file_path = self._absolute_upload_path(qr_code_path)
        return send_file(file_path, mimetype='image/png', conditional=True)

    def public_download_ebook(self, ebook_id):
        ebook = self.book_repository.find_ebook(ebook_id)
        if not ebook:
            return jsonify({'message': 'E-book not found'}), 404

        file_path = self._resolve_ebook_file_path(ebook)
        if not file_path:
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

        file_path = self._resolve_ebook_file_path(deleted_ebook)
        if file_path:
            try:
                os.remove(file_path)
            except OSError as exc:
                return jsonify({
                    'message': 'E-book database record was deleted, but the stored file could not be removed.',
                    'detail': str(exc),
                }), 500

        return jsonify({'message': 'E-book deleted'}), 200

    def _resolve_ebook_file_path(self, ebook):
        if not ebook:
            return None

        upload_root = os.path.abspath(Config.EBOOK_UPLOAD_FOLDER)
        candidates = []
        file_path = str(ebook.get('file_path') or '').strip()
        if file_path:
            if os.path.isabs(file_path):
                candidates.append(file_path)
            else:
                candidates.append(os.path.abspath(file_path))
                repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
                candidates.append(os.path.abspath(os.path.join(repo_root, file_path)))
                candidates.append(os.path.abspath(os.path.join(upload_root, file_path)))

        stored_filename = str(ebook.get('stored_filename') or '').strip()
        if stored_filename:
            candidates.append(os.path.abspath(os.path.join(upload_root, stored_filename)))

        for candidate in candidates:
            try:
                if os.path.commonpath([upload_root, candidate]) == upload_root and os.path.exists(candidate):
                    return candidate
            except ValueError:
                continue

        return None

    def _frontend_base_url(self, data=None):
        data = data or {}
        explicit_base_url = (data.get('base_url') or request.args.get('base_url') or '').strip()
        if explicit_base_url:
            return explicit_base_url.rstrip('/')
        return request.host_url.rstrip('/')

    def _public_upload_url(self, relative_path):
        if not relative_path:
            return None
        normalized = str(relative_path).replace('\\', '/').lstrip('/')
        return f"/{normalized}"

    def _absolute_upload_path(self, relative_path):
        normalized = str(relative_path).replace('\\', '/').lstrip('/')
        prefix = 'uploads/qr_codes/'
        if not normalized.startswith(prefix):
            raise ValueError('Invalid QR code path')
        relative_inside_qr_root = normalized[len(prefix):]
        file_path = os.path.abspath(os.path.join(Config.QR_CODE_FOLDER, *relative_inside_qr_root.split('/')))
        qr_root = os.path.abspath(Config.QR_CODE_FOLDER)
        if os.path.commonpath([qr_root, file_path]) != qr_root:
            raise ValueError('Invalid QR code path')
        return file_path

    def _stored_qr_exists(self, relative_path):
        try:
            return os.path.isfile(self._absolute_upload_path(relative_path))
        except ValueError:
            return False

    def _generate_book_qr_code(self, book_id, base_url):
        detail_url = f"{base_url.rstrip('/')}/books/{book_id}"
        relative_path = f"uploads/qr_codes/books/book_{book_id}.png"
        file_path = self._absolute_upload_path(relative_path)
        self._write_qr_png(detail_url, file_path)
        self.book_repository.update_book_qr_code_path(book_id, relative_path)
        return relative_path

    def _generate_ebook_qr_code(self, ebook_id, base_url):
        detail_url = f"{base_url.rstrip('/')}/ebooks/{ebook_id}"
        relative_path = f"uploads/qr_codes/ebooks/ebook_{ebook_id}.png"
        file_path = self._absolute_upload_path(relative_path)
        self._write_qr_png(detail_url, file_path)
        self.book_repository.update_ebook_qr_code_path(ebook_id, relative_path)
        return relative_path

    def _write_qr_png(self, payload, file_path):
        import qrcode

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(payload)
        qr.make(fit=True)
        image = qr.make_image(fill_color='black', back_color='white')
        image.save(file_path)

    def _deterministic_qr_svg(self, payload: str, label: str):
        # Lightweight, dependency-free QR-style code. The encoded URL is embedded for scanners/apps that read the title.
        import hashlib

        digest = hashlib.sha256(payload.encode('utf-8')).digest()
        cell = 8
        size = 29
        margin = 4
        width = (size + margin * 2) * cell
        rects = []
        finder_positions = [(0, 0), (size - 7, 0), (0, size - 7)]

        def in_finder(x, y):
            return any(fx <= x < fx + 7 and fy <= y < fy + 7 for fx, fy in finder_positions)

        for fx, fy in finder_positions:
            for y in range(7):
                for x in range(7):
                    border = x in (0, 6) or y in (0, 6)
                    center = 2 <= x <= 4 and 2 <= y <= 4
                    if border or center:
                        rects.append((fx + x, fy + y))

        bit_index = 0
        for y in range(size):
            for x in range(size):
                if in_finder(x, y):
                    continue
                byte = digest[(bit_index // 8) % len(digest)]
                if (byte >> (bit_index % 8)) & 1:
                    rects.append((x, y))
                bit_index += 1

        rect_markup = ''.join(
            f'<rect x="{(x + margin) * cell}" y="{(y + margin) * cell}" width="{cell}" height="{cell}"/>'
            for x, y in rects
        )
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{width}" viewBox="0 0 {width} {width}" role="img">
<title>{escape(payload)}</title>
<rect width="100%" height="100%" fill="#fff"/>
<g fill="#111">{rect_markup}</g>
<text x="50%" y="{width - 8}" text-anchor="middle" font-size="10" font-family="Arial" fill="#111">{escape(label)}</text>
</svg>"""

    def _qrcode_svg(self, payload: str):
        try:
            import io
            import qrcode
            import qrcode.image.svg

            image = qrcode.make(payload, image_factory=qrcode.image.svg.SvgPathImage)
            buffer = io.BytesIO()
            image.save(buffer)
            return buffer.getvalue().decode('utf-8')
        except Exception:
            return None
