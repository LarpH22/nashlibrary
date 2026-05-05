from flask import Blueprint
from flask_jwt_extended import jwt_required

from ..controllers.fine_controller import FineController
from ..middlewares.auth_middleware import set_current_user

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


@fine_bp.route('/student', methods=['GET'], strict_slashes=False)
@jwt_required()
def list_student_fines():
    current_user = set_current_user()
    return controller.list_student_fines(current_user)


@fine_bp.route('/admin', methods=['GET'], strict_slashes=False)
@jwt_required()
def list_all_fines():
    current_user = set_current_user()
    return controller.list_all_fines(current_user)


@fine_bp.route('/<int:fine_id>/status', methods=['PATCH'], strict_slashes=False)
@jwt_required()
def update_fine_status(fine_id):
    current_user = set_current_user()
    return controller.update_fine_status(fine_id, current_user)


@fine_bp.route('/<int:fine_id>/payment', methods=['PATCH'], strict_slashes=False)
@jwt_required()
def review_fine_payment(fine_id):
    current_user = set_current_user()
    return controller.review_fine_payment(fine_id, current_user)
