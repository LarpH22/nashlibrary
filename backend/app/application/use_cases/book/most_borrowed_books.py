from ....domain.repositories.book_repository import BookRepository


class MostBorrowedBooksUseCase:
    def __init__(self, book_repository: BookRepository):
        self.book_repository = book_repository

    def execute(self, limit: int = 5):
        return self.book_repository.most_borrowed_books(limit=limit)
