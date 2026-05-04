import random
from datetime import date
from typing import Any

from ..repositories.seed_repository import SeedRepository


class BookSeedService:
    STATUS_OPTIONS = ['available', 'borrowed', 'lost', 'maintenance']
    CATEGORY_NAMES = [
        'History', 'Science', 'Technology', 'Literature', 'Education', 'Art', 'Business',
        'Philosophy', 'Mathematics', 'Travel', 'Health', 'Psychology', 'Environment',
        'Politics', 'Self-Help', 'Fantasy', 'Biography', 'Engineering', 'Law', 'Music'
    ]
    AUTHOR_FIRST_NAMES = [
        'Avery', 'Jordan', 'Morgan', 'Taylor', 'Riley', 'Cameron', 'Alex', 'Casey', 'Jamie', 'Reese',
        'Brook', 'Drew', 'Quinn', 'Harper', 'Parker', 'Sydney', 'Hayden', 'Emerson', 'Rowan', 'Blake'
    ]
    AUTHOR_LAST_NAMES = [
        'Reid', 'Palmer', 'Hawthorne', 'Carver', 'Morrison', 'Langley', 'Hutchinson', 'Davenport',
        'Sullivan', 'Briggs', 'Fairchild', 'Delaney', 'Montgomery', 'Chandler', 'Wells', 'Kennedy',
        'Bennett', 'Hartman', 'Ellison', 'Rowley'
    ]
    TITLE_ADJECTIVES = [
        'Silent', 'Hidden', 'Lost', 'Golden', 'Winter', 'Electric', 'Ancient', 'Midnight', 'Sacred',
        'Secret', 'Crimson', 'Wise', 'Broken', 'Infinite', 'Fading', 'Brave', 'Quiet', 'Final', 'Bright',
        'Last'
    ]
    TITLE_NOUNS = [
        'Empire', 'Memory', 'Horizon', 'Journey', 'Legacy', 'Equation', 'Garden', 'River', 'Promise',
        'Threshold', 'Voyage', 'Chapter', 'City', 'Wild', 'Spectrum', 'Odyssey', 'Mirage', 'Code', 'Notebook',
        'Symphony'
    ]
    TITLE_SUBJECTS = [
        'Design', 'Leadership', 'Ecology', 'Ethics', 'Innovation', 'Modernity', 'Astronomy', 'Culture',
        'Economics', 'Architecture', 'Medicine', 'Narrative', 'Society', 'Creativity', 'Adventure',
        'Politics', 'Consciousness', 'Networks', 'Frontiers', 'Discovery'
    ]

    def __init__(self, repository: SeedRepository):
        self.repository = repository

    def seed_books(self, book_count: int = 500) -> dict[str, Any]:
        self.repository.ensure_inventory_schema()
        existing_isbns = self.repository.get_existing_book_isbns()
        all_books = self._build_book_records(book_count)

        metrics = {
            'requested': book_count,
            'inserted_books': 0,
            'skipped_existing_books': 0,
            'inserted_copies': 0,
        }

        def _seed_transaction(conn):
            for book in all_books:
                if book['isbn'] in existing_isbns:
                    metrics['skipped_existing_books'] += 1
                    continue

                author_id = self.repository.get_or_create_author(book['author'], conn=conn)
                category_id = self.repository.get_or_create_category(book['category'], conn=conn)
                book_id = self.repository.create_book(
                    title=book['title'],
                    author_id=author_id,
                    category_id=category_id,
                    isbn=book['isbn'],
                    published_date=book['published_date'],
                    cover_image_url=book['cover_image_url'],
                    conn=conn,
                )

                for copy in book['copies']:
                    self.repository.create_book_copy(
                        book_id,
                        copy['copy_code'],
                        copy['status'],
                        copy['location'],
                        conn=conn,
                    )
                    metrics['inserted_copies'] += 1

                metrics['inserted_books'] += 1

            return metrics

        return self.repository.run_in_transaction(_seed_transaction)

    def _build_book_records(self, book_count: int) -> list[dict[str, Any]]:
        generated_isbns = self._generate_unique_isbns(book_count)
        records = []

        for isbn in generated_isbns:
            title = self._generate_title()
            author = self._generate_author_name()
            category = random.choice(self.CATEGORY_NAMES)
            total_copies = random.randint(3, 8)
            records.append({
                'isbn': isbn,
                'title': title,
                'author': author,
                'category': category,
                'published_date': self._generate_published_date(),
                'cover_image_url': self._build_cover_image_url(isbn),
                'copies': self._generate_book_copies(isbn, total_copies),
            })

        return records

    def _generate_unique_isbns(self, count: int) -> list[str]:
        unique_isbns = set()
        while len(unique_isbns) < count:
            prefix = random.choice(['978', '979'])
            body = ''.join(str(random.randint(0, 9)) for _ in range(9))
            candidate = prefix + body
            check_digit = self._isbn13_check_digit(candidate)
            unique_isbns.add(f"{candidate}{check_digit}")
        return list(unique_isbns)

    def _isbn13_check_digit(self, digits12: str) -> int:
        total = 0
        for index, char in enumerate(digits12):
            weight = 1 if index % 2 == 0 else 3
            total += int(char) * weight
        remainder = total % 10
        return 0 if remainder == 0 else 10 - remainder

    def _generate_title(self) -> str:
        adjective = random.choice(self.TITLE_ADJECTIVES)
        noun = random.choice(self.TITLE_NOUNS)
        subject = random.choice(self.TITLE_SUBJECTS)
        pattern = random.choice([
            '{adjective} {noun}',
            '{subject} of the {noun}',
            '{adjective} {subject}',
            '{noun} of {subject}',
            'The {noun} of {adjective} {subject}',
        ])
        return pattern.format(adjective=adjective, noun=noun, subject=subject)

    def _generate_author_name(self) -> str:
        return f"{random.choice(self.AUTHOR_FIRST_NAMES)} {random.choice(self.AUTHOR_LAST_NAMES)}"

    def _generate_published_date(self):
        year = random.randint(1950, date.today().year)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        return date(year, month, day)

    def _build_cover_image_url(self, isbn: str) -> str:
        return f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"

    def _generate_book_copies(self, isbn: str, total_copies: int) -> list[dict[str, str]]:
        copies = []
        for copy_index in range(1, total_copies + 1):
            copies.append({
                'copy_code': f"BC-{isbn[-4:]}-{copy_index:02d}",
                'status': random.choices(self.STATUS_OPTIONS, weights=[0.7, 0.18, 0.08, 0.04], k=1)[0],
                'location': self._generate_copy_location(),
            })
        return copies

    def _generate_copy_location(self) -> str:
        floor = random.randint(1, 4)
        section = random.choice(['A', 'B', 'C', 'D', 'E', 'F'])
        shelf = random.randint(1, 24)
        return f"Floor {floor}-{section}{shelf:02d}"
