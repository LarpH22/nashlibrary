from flask import jsonify, request

from ...domain.services.book_seed_service import BookSeedService
from ...infrastructure.repositories_impl.seed_repository_impl import SeedRepositoryImpl


class SeedController:
    def __init__(self):
        self.service = BookSeedService(SeedRepositoryImpl())

    def seed_books(self):
        payload = request.get_json(silent=True) or {}
        count = payload.get('count', payload.get('book_count', 500))
        try:
            count = int(count)
        except (TypeError, ValueError):
            count = 500

        count = max(1, min(1000, count))
        metrics = self.service.seed_books(book_count=count)
        return jsonify({
            'message': 'Library seed completed',
            'metrics': metrics,
            'seed_endpoint': '/api/seed/books',
        }), 200
