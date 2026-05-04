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
