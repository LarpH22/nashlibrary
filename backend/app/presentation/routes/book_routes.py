from flask import Blueprint
from flask_jwt_extended import jwt_required

from ..controllers.book_controller import BookController
from ..middlewares.auth_middleware import set_current_user

book_bp = Blueprint('book', __name__)
controller = BookController()


@book_bp.route('/', methods=['GET'], strict_slashes=False)
def list_books():
    return controller.list_books()


@book_bp.route('/', methods=['POST'], strict_slashes=False)
def add_book():
    return controller.add_book()


@book_bp.route('/borrow', methods=['POST'], strict_slashes=False)
@jwt_required()
def borrow_book():
    return controller.borrow_book(set_current_user())


@book_bp.route('/borrow-requests', methods=['GET'], strict_slashes=False)
@jwt_required()
def list_borrow_requests():
    return controller.list_borrow_requests(set_current_user())


@book_bp.route('/borrow-requests/<int:request_id>/approve', methods=['POST'], strict_slashes=False)
@jwt_required()
def approve_borrow_request(request_id):
    return controller.approve_borrow_request(request_id, set_current_user())


@book_bp.route('/borrow-requests/<int:request_id>/reject', methods=['POST'], strict_slashes=False)
@jwt_required()
def reject_borrow_request(request_id):
    return controller.reject_borrow_request(request_id, set_current_user())


@book_bp.route('/return', methods=['POST'], strict_slashes=False)
@jwt_required()
def return_book():
    return controller.return_book(set_current_user())


@book_bp.route('/copies', methods=['GET'], strict_slashes=False)
@jwt_required()
def list_book_copies():
    return controller.list_book_copies(set_current_user())


@book_bp.route('/scan', methods=['GET', 'POST'], strict_slashes=False)
@jwt_required()
def lookup_copy_by_scan():
    return controller.lookup_copy_by_scan(set_current_user())


@book_bp.route('/borrow-by-scan', methods=['POST'], strict_slashes=False)
@jwt_required()
def borrow_by_scan():
    return controller.borrow_by_scan(set_current_user())


@book_bp.route('/return-by-scan', methods=['POST'], strict_slashes=False)
@jwt_required()
def return_by_scan():
    return controller.return_by_scan(set_current_user())


@book_bp.route('/copies/<int:copy_id>/qr.svg', methods=['GET'], strict_slashes=False)
def copy_qr_svg(copy_id):
    return controller.copy_qr_svg(copy_id)


@book_bp.route('/qr-codes/generate', methods=['POST'], strict_slashes=False)
@jwt_required()
def bulk_generate_book_qr_codes():
    return controller.bulk_generate_book_qr_codes(set_current_user())


@book_bp.route('/<int:book_id>/detail', methods=['GET'], strict_slashes=False)
def book_detail(book_id):
    return controller.book_detail(book_id)


@book_bp.route('/<int:book_id>/qr.svg', methods=['GET'], strict_slashes=False)
def book_qr_svg(book_id):
    return controller.book_qr_svg(book_id)


@book_bp.route('/<int:book_id>/qr.png', methods=['GET'], strict_slashes=False)
def book_qr_png(book_id):
    return controller.book_qr_png(book_id)


@book_bp.route('/ebooks', methods=['GET'], strict_slashes=False)
@jwt_required()
def list_ebooks():
    return controller.list_ebooks(set_current_user())


@book_bp.route('/ebooks', methods=['POST'], strict_slashes=False)
@jwt_required()
def upload_ebook():
    return controller.upload_ebook(set_current_user())


@book_bp.route('/ebooks/<int:ebook_id>/download', methods=['GET'], strict_slashes=False)
@jwt_required()
def download_ebook(ebook_id):
    return controller.download_ebook(ebook_id, set_current_user())


@book_bp.route('/ebooks/<int:ebook_id>/detail', methods=['GET'], strict_slashes=False)
def ebook_detail(ebook_id):
    return controller.ebook_detail(ebook_id)


@book_bp.route('/ebooks/<int:ebook_id>/qr.svg', methods=['GET'], strict_slashes=False)
def ebook_qr_svg(ebook_id):
    return controller.ebook_qr_svg(ebook_id)


@book_bp.route('/ebooks/<int:ebook_id>/qr.png', methods=['GET'], strict_slashes=False)
def ebook_qr_png(ebook_id):
    return controller.ebook_qr_png(ebook_id)


@book_bp.route('/ebooks/<int:ebook_id>/public-download', methods=['GET'], strict_slashes=False)
def public_download_ebook(ebook_id):
    return controller.public_download_ebook(ebook_id)


@book_bp.route('/ebooks/<int:ebook_id>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
def delete_ebook(ebook_id):
    return controller.delete_ebook(ebook_id, set_current_user())
