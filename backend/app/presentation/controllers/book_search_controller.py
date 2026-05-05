from flask import jsonify, request
import math

from ...application.use_cases.book.most_borrowed_books import MostBorrowedBooksUseCase
from ...application.use_cases.book.search_books import SearchBooksUseCase
from ...infrastructure.repositories_impl.book_repository_impl import BookRepositoryImpl


class BookSearchController:
    def __init__(self):
        self.book_repository = BookRepositoryImpl()
        self.search_books_use_case = SearchBooksUseCase(self.book_repository)
        self.most_borrowed_books_use_case = MostBorrowedBooksUseCase(self.book_repository)

    def search_books(self):
        title = request.args.get('title', '').strip()
        keyword = request.args.get('query', '').strip()
        author = request.args.get('author', '').strip()
        category = request.args.get('category', '').strip()
        isbn = request.args.get('isbn', '').strip()
        availability = request.args.get('availability', '').strip().lower()
        history = request.args.get('history', '').strip().lower()
        page = max(1, request.args.get('page', 1, type=int) or 1)
        limit = request.args.get('limit', 10, type=int) or 10
        limit = max(1, min(limit, 100))

        search_title = title or keyword

        result = self.search_books_use_case.execute(
            title=search_title,
            author=author,
            category=category,
            isbn=isbn,
            availability=availability,
            history=history,
            page=page,
            limit=limit,
        )

        if isinstance(result, dict):
            for book in result.get('books', []):
                self._attach_book_links(book)
            return jsonify(result), 200

        total = len(result)
        for book in result:
            self._attach_book_links(book)
        return jsonify({
            'books': result,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': max(1, math.ceil(total / limit)),
            },
        }), 200

    def most_borrowed_books(self):
        limit = request.args.get('limit', 5, type=int)
        books = self.most_borrowed_books_use_case.execute(limit=limit)
        for book in books:
            self._attach_book_links(book)
        return jsonify({'books': books}), 200

    def _attach_book_links(self, book):
        book_id = book.get('book_id') or book.get('id')
        if not book_id:
            return
        book['detail_url'] = f"/books/{book_id}"
