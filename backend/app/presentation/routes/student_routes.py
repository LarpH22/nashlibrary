from flask import Blueprint
from flask_jwt_extended import jwt_required

from ..controllers.student_controller import StudentController
from ..middlewares.auth_middleware import set_current_user

student_bp = Blueprint('student', __name__)
controller = StudentController()


@student_bp.route('/profile', methods=['GET'], strict_slashes=False)
@jwt_required()
def profile():
    current_user = set_current_user()
    return controller.profile(current_user)


@student_bp.route('/profile', methods=['PUT'], strict_slashes=False)
@jwt_required()
def update_profile():
    current_user = set_current_user()
    return controller.update_profile(current_user)
