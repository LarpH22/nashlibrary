from flask import Blueprint

from ..controllers.seed_controller import SeedController

seed_bp = Blueprint('seed', __name__)
controller = SeedController()

@seed_bp.route('/books', methods=['POST', 'GET'], strict_slashes=False)
def seed_books():
    """Seed normalized book inventory data safely and idempotently."""
    return controller.seed_books()
