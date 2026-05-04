from flask import Blueprint

from ..controllers.book_search_controller import BookSearchController

book_search_bp = Blueprint('book_search', __name__)
controller = BookSearchController()

@book_search_bp.route('/search', methods=['GET'], strict_slashes=False)
def search_books():
    return controller.search_books()

@book_search_bp.route('/most-borrowed', methods=['GET'], strict_slashes=False)
def most_borrowed_books():
    return controller.most_borrowed_books()
