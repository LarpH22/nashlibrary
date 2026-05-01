import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from .infrastructure.config import Config
from .presentation.routes import register_blueprints
from .presentation.middlewares.auth_middleware import jwt_manager
from .presentation.middlewares.error_handler import register_error_handlers


def create_app(config_object=None):
    dist_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'dist'))
    static_folder = dist_folder if os.path.isdir(dist_folder) else None
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_object or Config)
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
    app.config['PROPAGATE_EXCEPTIONS'] = True

    CORS(app)
    jwt_manager.init_app(app)

    register_blueprints(app)
    register_error_handlers(app)

    @app.route('/register', methods=['GET'])
    @app.route('/login', methods=['GET'])
    def serve_auth_pages():
        if static_folder:
            return send_from_directory(static_folder, 'index.html')
        return jsonify({'message': 'Backend is running', 'status': 'ok'})

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if static_folder:
            requested_path = path or 'index.html'
            full_path = os.path.join(static_folder, requested_path)
            if path and os.path.exists(full_path):
                return send_from_directory(static_folder, requested_path)
            return send_from_directory(static_folder, 'index.html')

        return jsonify({'message': 'Backend is running', 'status': 'ok'})

    return app


app = create_app()
