from flask import Blueprint
from flask_jwt_extended import jwt_required

from ..controllers.fine_controller import FineController

fine_bp = Blueprint('fine', __name__)
controller = FineController()


@fine_bp.route('/calculate', methods=['GET'], strict_slashes=False)
@jwt_required()
def calculate_fine():
    return controller.calculate_fine()


@fine_bp.route('/pay', methods=['POST'], strict_slashes=False)
@jwt_required()
def pay_fine():
    return controller.pay_fine()
