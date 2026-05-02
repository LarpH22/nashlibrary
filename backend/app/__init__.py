import os
import socket
from flask import Flask, jsonify, send_from_directory, redirect, request
from flask_cors import CORS

from .infrastructure.config import Config
from .presentation.routes import register_blueprints
from .presentation.middlewares.auth_middleware import jwt_manager
from .presentation.middlewares.error_handler import register_error_handlers
from .infrastructure.external.email_service import EmailService


def create_app(config_object=None):
    dist_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'dist'))
    static_folder = dist_folder if os.path.isdir(dist_folder) else None
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_object or Config)
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
    app.config['PROPAGATE_EXCEPTIONS'] = True

    CORS(app)
    jwt_manager.init_app(app)

    # Initialize email service
    email_service = EmailService(app)

    # Important: Register blueprints FIRST
    register_blueprints(app)
    register_error_handlers(app)

    # Get configuration for frontend serving
    use_dev_frontend = os.environ.get('USE_DEV_FRONTEND', 'true').lower() in ['true', '1', 'yes']
    configured_frontend_url = app.config.get('FRONTEND_URL', 'http://localhost:3000')

    def find_frontend_url() -> str | None:
        if not use_dev_frontend:
            return configured_frontend_url

        candidate_ports = [3000, 3001, 3002, 3003, 3004]
        for port in candidate_ports:
            try:
                with socket.create_connection(('127.0.0.1', port), timeout=0.25):
                    return f'http://127.0.0.1:{port}'
            except OSError:
                continue
        return None

    def get_dev_frontend_url(path=''):
        base_url = find_frontend_url()
        if not base_url:
            return None
        if path:
            return f"{base_url}/{path.lstrip('/')}"
        return base_url

    # Explicitly register routes AFTER blueprints to ensure they have priority
    @app.route('/register', methods=['GET'])
    @app.route('/login', methods=['GET'])
    def serve_auth_pages():
        dev_url = get_dev_frontend_url(request.path) if use_dev_frontend else None
        print(f"serve_auth_pages called: path={request.path} dev_url={dev_url}")
        if dev_url:
            return redirect(dev_url, code=302)
        if static_folder:
            return send_from_directory(static_folder, 'index.html')
        return jsonify({'message': 'Backend is running', 'status': 'ok'})

    @app.route('/', defaults={'path': ''}, methods=['GET'])
    @app.route('/<path:path>', methods=['GET'])
    def serve_frontend(path):
        print(f"serve_frontend called: path={path}")
        if path.startswith('api/'):
            return jsonify({'message': 'Endpoint not found', 'status': 404}), 404

        dev_url = get_dev_frontend_url(path or '/') if use_dev_frontend else None
        print(f"serve_frontend dev_url={dev_url}")
        if dev_url:
            return redirect(dev_url, code=302)
        if static_folder:
            requested_path = path or 'index.html'
            full_path = os.path.join(static_folder, requested_path)
            if path and os.path.exists(full_path):
                return send_from_directory(static_folder, requested_path)
            return send_from_directory(static_folder, 'index.html')
        return jsonify({'message': 'Backend is running', 'status': 'ok'})

    print(f"\n=== Routes Registered ===")
    print(f"Total routes: {len(list(app.url_map.iter_rules()))}")
    for rule in app.url_map.iter_rules():
        if rule.rule in ['/register', '/login', '/', '/<path:path>']:
            print(f"  {rule.rule} -> {rule.endpoint}")
    print(f"========================\n")

    return app


app = create_app()

