from abc import ABC, abstractmethod


class BookRepository(ABC):
    @abstractmethod
    def add_book(self, title: str, author: str, isbn: str, available_copies: int = 1, total_copies: int = 1):
        raise NotImplementedError

    @abstractmethod
    def list_books(self):
        raise NotImplementedError

    @abstractmethod
    def find_by_id(self, book_id: int):
        raise NotImplementedError

    @abstractmethod
    def search_books(
        self,
        title: str = '',
        author: str = '',
        category: str = '',
        isbn: str = '',
        availability: str = '',
        history: str = '',
    ):
        raise NotImplementedError

    @abstractmethod
    def update_book_status(self, book_id: int, status: str, available_copies: int | None = None):
        raise NotImplementedError
