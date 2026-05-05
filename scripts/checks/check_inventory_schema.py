from backend.app.infrastructure.database.db_connection import get_connection
from backend.app.infrastructure.repositories_impl.book_repository_impl import BookRepositoryImpl


def main():
    rows = BookRepositoryImpl().search_books()
    print("books", len(rows))
    print("sample", rows[:3])

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DESC book_copies")
            print("book_copies columns", [row["Field"] for row in cur.fetchall()])

            cur.execute("DESC borrow_records")
            print("borrow_records columns", [row["Field"] for row in cur.fetchall()])

            cur.execute("SELECT status, COUNT(*) AS count FROM book_copies GROUP BY status")
            print("copy statuses", cur.fetchall())


if __name__ == "__main__":
    main()
