from abc import ABC, abstractmethod


class SeedRepository(ABC):
    @abstractmethod
    def ensure_inventory_schema(self):
        raise NotImplementedError

    @abstractmethod
    def get_existing_book_isbns(self) -> set:
        raise NotImplementedError

    @abstractmethod
    def get_or_create_author(self, name: str, conn=None) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_or_create_category(self, name: str, conn=None) -> int:
        raise NotImplementedError

    @abstractmethod
    def create_book(self, title: str, author_id: int, category_id: int, isbn: str, published_date, cover_image_url: str, conn=None) -> int:
        raise NotImplementedError

    @abstractmethod
    def create_book_copy(self, book_id: int, copy_code: str, status: str, location: str, conn=None) -> int:
        raise NotImplementedError

    @abstractmethod
    def run_in_transaction(self, callback):
        raise NotImplementedError
