from ....domain.services.library_service import LibraryService


class BorrowBookUseCase:
    def __init__(self, library_service: LibraryService):
        self.library_service = library_service

    def execute(self, book_id: int, user_id: int, borrowed_at, due_date):
        return self.library_service.borrow_book(book_id, user_id, borrowed_at, due_date)
