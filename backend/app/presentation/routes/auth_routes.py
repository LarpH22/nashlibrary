from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..controllers.auth_controller import AuthController


auth_bp = Blueprint('auth', __name__)
controller = AuthController()


@auth_bp.route('/register', methods=['POST'], strict_slashes=False)
def register():
    return controller.register()


@auth_bp.route('/verify-email', methods=['GET'], strict_slashes=False)
def verify_email():
    return controller.verify_email()


@auth_bp.route('/approve-registration', methods=['POST'], strict_slashes=False)
@jwt_required()
def approve_registration():
    return controller.approve_registration()


@auth_bp.route('/login', methods=['POST'], strict_slashes=False)
def login():
    return controller.login()


@auth_bp.route('/forgot-password', methods=['POST'], strict_slashes=False)
def forgot_password():
    return controller.forgot_password()


@auth_bp.route('/reset-password', methods=['POST'], strict_slashes=False)
def reset_password():
    return controller.reset_password()


@auth_bp.route('/profile', methods=['GET'], strict_slashes=False)
@jwt_required()
def profile():
    """Get the profile of the authenticated user using JWT identity."""
    from flask_jwt_extended import get_jwt
    jwt_claims = get_jwt()
    
    email = jwt_claims.get('email')
    role = jwt_claims.get('role')
    
    profile_data = controller.get_profile_use_case.execute(email, role)
    if not profile_data:
        return jsonify({'message': 'User not found'}), 404
    return jsonify(profile_data), 200
