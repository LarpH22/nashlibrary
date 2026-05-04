from ....domain.repositories.book_repository import BookRepository


class SearchBooksUseCase:
    def __init__(self, book_repository: BookRepository):
        self.book_repository = book_repository

    def execute(
        self,
        title: str = '',
        author: str = '',
        category: str = '',
        isbn: str = '',
        availability: str = '',
        history: str = '',
        page: int | None = None,
        limit: int | None = None,
    ):
        return self.book_repository.search_books(
            title=title,
            author=author,
            category=category,
            isbn=isbn,
            availability=availability,
            history=history,
            page=page,
            limit=limit,
        )
