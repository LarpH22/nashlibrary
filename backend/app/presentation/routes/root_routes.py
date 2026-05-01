from flask import Blueprint

root_bp = Blueprint('root', __name__)

@root_bp.route('/health', methods=['GET'])
def health():
    return {'status': 'ok', 'message': 'healthy'}, 200
