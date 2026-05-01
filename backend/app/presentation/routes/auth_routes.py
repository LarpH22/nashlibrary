from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..controllers.auth_controller import AuthController


auth_bp = Blueprint('auth', __name__)
controller = AuthController()


@auth_bp.route('/register', methods=['POST'])
def register():
    return controller.register()


@auth_bp.route('/login', methods=['POST'])
def login():
    return controller.login()


@auth_bp.route('/profile', methods=['GET'])
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
