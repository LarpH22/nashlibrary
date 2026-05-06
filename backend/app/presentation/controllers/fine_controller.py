import os
from uuid import uuid4

from flask import jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from ...application.use_cases.fine.calculate_fine import CalculateFineUseCase
from ...application.use_cases.fine.pay_fine import PayFineUseCase
from ...domain.services.fine_service import FineService
from ...infrastructure.config import Config
from ...infrastructure.repositories_impl.loan_repository_impl import LoanRepositoryImpl


class FineController:
    def __init__(self):
        self.loan_repository = LoanRepositoryImpl()
        self.fine_service = FineService(self.loan_repository)
        self.calculate_fine_use_case = CalculateFineUseCase(self.fine_service)
        self.pay_fine_use_case = PayFineUseCase(self.fine_service)

    def _parse_pagination_params(self):
        page = request.args.get('page', type=int)
        limit = request.args.get('limit', type=int)
        paginate = page is not None or limit is not None
        page = page if page and page > 0 else 1
        limit = limit if limit and limit > 0 else 15
        offset = (page - 1) * limit
        return page, limit, offset, paginate

    def _parse_loan_id(self, loan_id):
        if not loan_id:
            return None, (jsonify({'message': 'loan_id is required'}), 400)
        try:
            loan_id = int(loan_id)
        except (TypeError, ValueError):
            return None, (jsonify({'message': 'loan_id must be a valid integer'}), 400)
        if loan_id <= 0:
            return None, (jsonify({'message': 'loan_id must be greater than zero'}), 400)
        return loan_id, None

    def _validate_receipt_upload(self, receipt):
        if not receipt or not receipt.filename:
            return None, 'Receipt/proof of payment is required for online payments'

        filename = secure_filename(receipt.filename)
        if not filename or '.' not in filename:
            return None, 'Receipt must be a JPG, PNG, or PDF file'

        extension = filename.rsplit('.', 1)[1].lower()
        if extension not in {'jpg', 'jpeg', 'png', 'pdf'}:
            return None, 'Receipt must be a JPG, PNG, or PDF file'

        receipt.stream.seek(0, os.SEEK_END)
        size = receipt.stream.tell()
        receipt.stream.seek(0)
        if size <= 0:
            return None, 'Receipt file cannot be empty'
        if size > 5 * 1024 * 1024:
            return None, 'Receipt file must be 5 MB or smaller'

        receipt_dir = os.path.join(Config.UPLOAD_FOLDER, 'fine_receipts')
        os.makedirs(receipt_dir, exist_ok=True)
        stored_name = f"{uuid4().hex}.{extension}"
        stored_path = os.path.join(receipt_dir, stored_name)
        receipt.save(stored_path)
        return {
            'receipt_path': os.path.join('fine_receipts', stored_name).replace('\\', '/'),
            'receipt_filename': filename,
            'receipt_size': size,
        }, None

    def calculate_fine(self):
        loan_id, error_response = self._parse_loan_id(request.args.get('loan_id'))
        if error_response:
            return error_response

        fine_state = self.fine_service.get_fine_state_for_loan(loan_id)
        if not fine_state:
            return jsonify({'message': 'Loan not found'}), 404

        fine = self.calculate_fine_use_case.execute(loan_id)
        message = 'Fine calculated'
        if fine_state.get('status') == 'paid':
            message = 'Fine already paid'
        elif fine <= 0:
            message = 'No fine exists for this loan'

        return jsonify({
            'message': message,
            'loan_id': loan_id,
            'fine_amount': fine,
            'status': fine_state.get('status'),
            'days_overdue': fine_state.get('days_overdue', 0),
        }), 200

    def pay_fine(self):
        is_multipart = request.content_type and request.content_type.startswith('multipart/form-data')
        data = request.form if is_multipart else (request.get_json() or {})
        loan_id, error_response = self._parse_loan_id(data.get('loan_id'))
        if error_response:
            return error_response
        payment_method = (data.get('payment_method') or data.get('method') or 'online').strip().lower()
        if payment_method not in ['cash', 'online']:
            return jsonify({'message': 'payment_method must be cash or online'}), 400
        payment_reference = (data.get('payment_reference') or '').strip()

        fine_state = self.fine_service.get_fine_state_for_loan(loan_id)
        if not fine_state:
            return jsonify({'message': 'Loan not found'}), 404
        if fine_state.get('status') == 'paid':
            return jsonify({'message': 'Fine already paid'}), 409
        if fine_state.get('status') != 'unpaid' or fine_state.get('payable_amount', 0) <= 0:
            return jsonify({'message': 'No fine exists for this loan'}), 404

        receipt_data = None
        if payment_method == 'online':
            if not is_multipart:
                return jsonify({'message': 'Receipt/proof of payment is required for online payments'}), 400
            receipt_data, receipt_error = self._validate_receipt_upload(request.files.get('receipt'))
            if receipt_error:
                return jsonify({'message': receipt_error}), 400

        try:
            payment = self.loan_repository.create_fine_payment(
                loan_id,
                payment_method,
                payment_reference or None,
                receipt_data,
            )
        except ValueError as exc:
            if receipt_data:
                try:
                    os.remove(os.path.join(Config.UPLOAD_FOLDER, receipt_data['receipt_path']))
                except OSError:
                    pass
            return jsonify({'message': str(exc)}), 409
        except Exception:
            if receipt_data:
                try:
                    os.remove(os.path.join(Config.UPLOAD_FOLDER, receipt_data['receipt_path']))
                except OSError:
                    pass
            raise
        if not payment:
            if receipt_data:
                try:
                    os.remove(os.path.join(Config.UPLOAD_FOLDER, receipt_data['receipt_path']))
                except OSError:
                    pass
            return jsonify({'message': 'No fine exists for this loan'}), 404
        message = 'Cash payment submitted. Please wait for librarian or admin confirmation.'
        if payment_method == 'online':
            message = 'Online payment submitted. Please wait for verification.'
        return jsonify({'message': message, 'payment': payment}), 200

    def preview_fine_payment(self):
        data = request.get_json() or {}
        loan_id, error_response = self._parse_loan_id(data.get('loan_id'))
        if error_response:
            return error_response
        payment_method = (data.get('payment_method') or data.get('method') or 'online').strip().lower()
        if payment_method not in ['cash', 'online']:
            return jsonify({'message': 'payment_method must be cash or online'}), 400

        fine_state = self.fine_service.get_fine_state_for_loan(loan_id)
        if not fine_state:
            return jsonify({'message': 'Loan not found'}), 404
        if fine_state.get('status') == 'paid':
            return jsonify({'message': 'Fine already paid'}), 409
        if fine_state.get('status') != 'unpaid' or fine_state.get('payable_amount', 0) <= 0:
            return jsonify({'message': 'No fine exists for this loan'}), 404

        try:
            payment = self.loan_repository.preview_fine_payment(loan_id, payment_method)
        except ValueError as exc:
            return jsonify({'message': str(exc)}), 409
        if not payment:
            return jsonify({'message': 'No fine exists for this loan'}), 404

        return jsonify({
            'message': 'Payment preview generated. No payment status was changed.',
            'payment': payment
        }), 200

    def list_student_fines(self, current_user):
        if not current_user or current_user.get('role') != 'student':
            return jsonify({'message': 'Student access is required'}), 403

        student_id = current_user.get('student_id')
        try:
            student_id = int(student_id)
        except (TypeError, ValueError):
            return jsonify({'message': 'Student profile not found'}), 404

        page, limit, offset, paginate = self._parse_pagination_params()
        fines = self.fine_service.list_student_fines(student_id)
        unpaid = [fine for fine in fines if fine.get('status') in ('unpaid', 'pending')]
        paid = [fine for fine in fines if fine.get('status') == 'paid']
        waived = [fine for fine in fines if fine.get('status') == 'waived']
        pending = [fine for fine in fines if fine.get('payment_status') in ('pending', 'pending_verification')]
        total = len(fines)
        if paginate:
            fines = fines[offset:offset + limit]

        result = {
            'message': 'Student fines loaded',
            'fines': fines,
            'summary': {
                'total_count': total,
                'unpaid_count': len(unpaid),
                'paid_count': len(paid),
                'waived_count': len(waived),
                'pending_count': len(pending),
                'total_unpaid': round(sum(float(fine.get('amount') or 0) for fine in unpaid), 2),
                'total_paid': round(sum(float(fine.get('amount') or 0) for fine in paid), 2),
            }
        }
        if paginate:
            result['pagination'] = {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': max(1, (total + limit - 1) // limit)
            }
        return jsonify(result), 200

    def list_all_fines(self, current_user):
        if not current_user or current_user.get('role') not in ['admin', 'librarian']:
            return jsonify({'message': 'Admin or librarian access is required'}), 403

        page, limit, offset, paginate = self._parse_pagination_params()
        fines = self.loan_repository.find_all_fines()
        if current_user.get('role') != 'admin':
            for fine in fines:
                fine.pop('payment_receipt_path', None)
                fine.pop('payment_receipt_filename', None)
                fine.pop('payment_receipt_uploaded_at', None)
        unpaid = [fine for fine in fines if fine.get('status') == 'unpaid']
        pending = [fine for fine in fines if fine.get('payment_status') in ('pending', 'pending_verification')]
        paid = [fine for fine in fines if fine.get('status') == 'paid']
        waived = [fine for fine in fines if fine.get('status') == 'waived']
        total = len(fines)
        if paginate:
            fines = fines[offset:offset + limit]

        result = {
            'message': 'Fines loaded',
            'fines': fines,
            'summary': {
                'total_count': total,
                'unpaid_count': len(unpaid),
                'pending_count': len(pending),
                'paid_count': len(paid),
                'total_unpaid': round(sum(float(fine.get('amount') or 0) for fine in unpaid), 2),
                'total_paid': round(sum(float(fine.get('amount') or 0) for fine in paid), 2),
            }
        }
        if paginate:
            result['pagination'] = {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': max(1, (total + limit - 1) // limit)
            }
        return jsonify(result), 200

    def update_fine_status(self, fine_id, current_user):
        if not current_user or current_user.get('role') != 'admin':
            return jsonify({'message': 'Admin access is required'}), 403

        try:
            fine_id = int(fine_id)
        except (TypeError, ValueError):
            return jsonify({'message': 'fine_id must be a valid integer'}), 400
        if fine_id <= 0:
            return jsonify({'message': 'fine_id must be greater than zero'}), 400

        data = request.get_json() or {}
        status = data.get('status')
        try:
            fine = self.loan_repository.update_fine_status(fine_id, status)
        except ValueError as exc:
            return jsonify({'message': str(exc)}), 400

        if not fine:
            return jsonify({'message': 'Fine not found'}), 404

        return jsonify({'message': 'Fine status updated', 'fine': fine}), 200

    def review_fine_payment(self, fine_id, current_user):
        if not current_user or current_user.get('role') != 'admin':
            return jsonify({'message': 'Admin access is required'}), 403

        data = request.get_json() or {}
        action = data.get('action')
        try:
            fine = self.loan_repository.review_fine_payment(int(fine_id), action, current_user)
        except (TypeError, ValueError) as exc:
            return jsonify({'message': str(exc)}), 400

        if not fine:
            return jsonify({'message': 'Fine not found'}), 404

        message = 'Payment approved.' if action == 'approve' else 'Payment rejected.'
        return jsonify({'message': message, 'fine': fine}), 200

    def view_fine_receipt(self, fine_id, current_user):
        if not current_user or current_user.get('role') != 'admin':
            return jsonify({'message': 'Admin access is required'}), 403

        try:
            fine_id = int(fine_id)
        except (TypeError, ValueError):
            return jsonify({'message': 'fine_id must be a valid integer'}), 400

        receipt = self.loan_repository.get_fine_receipt(fine_id)
        receipt_path = (receipt or {}).get('payment_receipt_path')
        if not receipt_path:
            return jsonify({'message': 'Receipt not found'}), 404
        receipt_path = receipt_path.replace('\\', '/').lstrip('/')
        if receipt_path.startswith('../') or not receipt_path.startswith('fine_receipts/'):
            return jsonify({'message': 'Receipt path is invalid'}), 404

        receipt_dir = os.path.join(Config.UPLOAD_FOLDER, os.path.dirname(receipt_path))
        filename = os.path.basename(receipt_path)
        return send_from_directory(
            receipt_dir,
            filename,
            as_attachment=False,
            download_name=(receipt or {}).get('payment_receipt_filename') or filename,
        )
