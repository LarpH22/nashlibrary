from flask import Blueprint
from flask_jwt_extended import jwt_required

from ..controllers.admin_controller import AdminController

admin_bp = Blueprint('admin', __name__)
controller = AdminController()

@admin_bp.route('/categories', methods=['GET'])
@jwt_required()
def list_categories():
    return controller.list_categories()

@admin_bp.route('/categories', methods=['POST'])
@jwt_required()
def add_category():
    return controller.add_category()

@admin_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@jwt_required()
def delete_category(category_id):
    return controller.delete_category(category_id)

@admin_bp.route('/authors', methods=['GET'])
@jwt_required()
def list_authors():
    return controller.list_authors()

@admin_bp.route('/authors', methods=['POST'])
@jwt_required()
def add_author():
    return controller.add_author()

@admin_bp.route('/authors/<int:author_id>', methods=['DELETE'])
@jwt_required()
def delete_author(author_id):
    return controller.delete_author(author_id)

@admin_bp.route('/students/<int:student_id>', methods=['GET'])
@jwt_required()
def search_student(student_id):
    return controller.search_student(student_id)

@admin_bp.route('/registration-requests', methods=['GET'])
@jwt_required()
def list_registration_requests():
    return controller.list_registration_requests()

@admin_bp.route('/reject-registration', methods=['POST'])
@jwt_required()
def reject_registration():
    return controller.reject_registration()

@admin_bp.route('/loans', methods=['GET'])
@jwt_required()
def list_loans():
    return controller.list_loans()
