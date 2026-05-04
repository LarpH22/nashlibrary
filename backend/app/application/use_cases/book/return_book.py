from ....domain.services.library_service import LibraryService


class ReturnBookUseCase:
    def __init__(self, library_service: LibraryService):
        self.library_service = library_service

    def execute(self, loan_id: int, returned_at, student_id: int | None = None):
        return self.library_service.return_book(loan_id, returned_at, student_id)
