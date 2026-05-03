from flask import jsonify, request

from ...application.use_cases.book.search_books import SearchBooksUseCase
from ...infrastructure.repositories_impl.book_repository_impl import BookRepositoryImpl


class BookSearchController:
    def __init__(self):
        self.book_repository = BookRepositoryImpl()
        self.search_books_use_case = SearchBooksUseCase(self.book_repository)

    def search_books(self):
        title = request.args.get('title', '').strip()
        keyword = request.args.get('query', '').strip()
        author = request.args.get('author', '').strip()
        category = request.args.get('category', '').strip()
        isbn = request.args.get('isbn', '').strip()
        availability = request.args.get('availability', '').strip().lower()

        search_title = title or keyword

        books = self.search_books_use_case.execute(
            title=search_title,
            author=author,
            category=category,
            isbn=isbn,
            availability=availability
        )

        return jsonify({'books': books}), 200
