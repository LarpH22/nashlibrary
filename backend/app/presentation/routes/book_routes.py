from flask import Blueprint

from ..controllers.book_controller import BookController

book_bp = Blueprint('book', __name__)
controller = BookController()


@book_bp.route('/', methods=['GET'], strict_slashes=False)
def list_books():
    return controller.list_books()


@book_bp.route('/', methods=['POST'], strict_slashes=False)
def add_book():
    return controller.add_book()


@book_bp.route('/borrow', methods=['POST'], strict_slashes=False)
def borrow_book():
    return controller.borrow_book()


@book_bp.route('/return', methods=['POST'], strict_slashes=False)
def return_book():
    return controller.return_book()
