from ....domain.services.library_service import LibraryService


class AddBookUseCase:
    def __init__(self, library_service: LibraryService):
        self.library_service = library_service

    def execute(self, title: str, author: str, isbn: str, available_copies: int = 1, total_copies: int = 1):
        return self.library_service.add_book(title, author, isbn, available_copies, total_copies)
