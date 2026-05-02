from flask import Blueprint
from flask_jwt_extended import jwt_required

from ..controllers.user_controller import UserController

user_bp = Blueprint('user', __name__)
controller = UserController()


@user_bp.route('/profile', methods=['GET'], strict_slashes=False)
@jwt_required()
def profile():
    return controller.profile()
