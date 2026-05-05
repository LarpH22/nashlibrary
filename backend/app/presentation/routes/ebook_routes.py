from flask import Blueprint
from flask_jwt_extended import jwt_required

from ..controllers.book_controller import BookController
from ..middlewares.auth_middleware import set_current_user

ebook_bp = Blueprint('ebook', __name__)
controller = BookController()


@ebook_bp.route('', methods=['GET'], strict_slashes=False)
@ebook_bp.route('/', methods=['GET'], strict_slashes=False)
@jwt_required()
def list_ebooks():
    return controller.list_ebooks(set_current_user())


@ebook_bp.route('', methods=['POST'], strict_slashes=False)
@ebook_bp.route('/', methods=['POST'], strict_slashes=False)
@jwt_required()
def upload_ebook_root():
    return controller.upload_ebook(set_current_user())


@ebook_bp.route('/upload', methods=['POST'], strict_slashes=False)
@jwt_required()
def upload_ebook():
    return controller.upload_ebook(set_current_user())


@ebook_bp.route('/<int:ebook_id>/download', methods=['GET'], strict_slashes=False)
@jwt_required()
def download_ebook(ebook_id):
    return controller.download_ebook(ebook_id, set_current_user())


@ebook_bp.route('/<int:ebook_id>/public-download', methods=['GET'], strict_slashes=False)
def public_download_ebook(ebook_id):
    return controller.public_download_ebook(ebook_id)


@ebook_bp.route('/<int:ebook_id>/detail', methods=['GET'], strict_slashes=False)
def ebook_detail(ebook_id):
    return controller.ebook_detail(ebook_id)


@ebook_bp.route('/<int:ebook_id>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
def delete_ebook(ebook_id):
    return controller.delete_ebook(ebook_id, set_current_user())
