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
    frontend_folder = dist_folder if os.path.isdir(dist_folder) else None
    app = Flask(__name__, static_folder=None, static_url_path=None)
    app.config.from_object(config_object or Config)
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['FRONTEND_DIST_FOLDER'] = frontend_folder

    print(f'Frontend static folder: {frontend_folder}')
    CORS(app)
    jwt_manager.init_app(app)

    # Add security headers to prevent embedding and context issues
    @app.after_request
    def add_security_headers(response):
        # Prevent embedding in iframes
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; style-src-elem 'self' https://fonts.googleapis.com; img-src 'self' data: https:; font-src 'self' https://fonts.gstatic.com data:; connect-src 'self' http://localhost:* https://*; frame-ancestors 'none';"
        # Allow only same-origin and specific trusted origins
        response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        return response

    # Initialize email service
    email_service = EmailService(app)

    # Important: Register blueprints FIRST
    register_blueprints(app)
    register_error_handlers(app)

    # Get configuration for frontend serving
    use_dev_frontend = os.environ.get('USE_DEV_FRONTEND', 'false').lower() in ['true', '1', 'yes']
    configured_frontend_url = app.config.get('FRONTEND_URL', None)

    def find_frontend_url() -> str | None:
        if not use_dev_frontend:
            return None

        candidate_ports = [3000, 3001, 3002, 3003, 3004, 5173]
        candidate_hosts = ['127.0.0.1', 'localhost']
        for host in candidate_hosts:
            for port in candidate_ports:
                try:
                    with socket.create_connection((host, port), timeout=0.25):
                        return f'http://{host}:{port}'
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
    @app.route('/favicon.ico', methods=['GET'])
    def serve_favicon():
        frontend_dist = app.config.get('FRONTEND_DIST_FOLDER')
        if frontend_dist:
            icon_path = os.path.join(frontend_dist, 'favicon.ico')
            if os.path.exists(icon_path):
                return send_from_directory(frontend_dist, 'favicon.ico')
        return jsonify({'message': 'Favicon not found', 'status': 404}), 404

    def frontend_asset_response(path):
        frontend_dist = app.config.get('FRONTEND_DIST_FOLDER')
        if not frontend_dist or not path:
            return None

        normalized_path = path.replace('\\', '/')
        if '..' in normalized_path.split('/'):
            return None

        if not normalized_path.startswith('assets/'):
            normalized_path = f'assets/{normalized_path}'

        full_asset_path = os.path.join(frontend_dist, *normalized_path.split('/'))
        if os.path.isfile(full_asset_path):
            return send_from_directory(frontend_dist, normalized_path)
        return None

    @app.route('/assets/<path:path>', methods=['GET'])
    def serve_frontend_asset(path):
        asset_response = frontend_asset_response(path)
        if asset_response:
            return asset_response
        return jsonify({'message': 'Asset not found', 'status': 404}), 404

    @app.route('/uploads/qr_codes/<path:path>', methods=['GET'])
    def serve_qr_code(path):
        normalized_path = path.replace('\\', '/')
        if '..' in normalized_path.split('/'):
            return jsonify({'message': 'QR code not found', 'status': 404}), 404
        return send_from_directory(Config.QR_CODE_FOLDER, normalized_path)

    @app.route('/dashboard/api/<path:subpath>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
    def redirect_dashboard_api(subpath):
        """Redirect relative dashboard API paths to the root API path."""
        target = f"/api/{subpath}"
        return redirect(target, code=307)

    def serve_spa(path=''):
        """Serve SPA - always return index.html for frontend routes"""
        frontend_dist = app.config.get('FRONTEND_DIST_FOLDER')
        
        if use_dev_frontend:
            # Get the full URL with query parameters
            full_url = request.full_path
            dev_base = find_frontend_url()
            if dev_base:
                # Redirect to dev frontend with full path and query string preserved
                dev_url = f"{dev_base}{full_url.lstrip('/')}"
                print(f"Redirecting to dev frontend: {dev_url}")
                return redirect(dev_url, code=302)
        
        # Serve from built frontend
        if frontend_dist:
            # Always serve index.html for SPA routing to work
            return send_from_directory(frontend_dist, 'index.html')
        
        return jsonify({'message': 'Backend is running', 'status': 'ok'})

    # Register SPA routes - these should be handled by React Router
    @app.route('/register', methods=['GET'])
    @app.route('/login', methods=['GET'])
    @app.route('/verify-email', methods=['GET'])
    @app.route('/reset-password', methods=['GET'])
    def serve_auth_pages():
        return serve_spa()

    @app.route('/dashboard', defaults={'subpath': ''}, methods=['GET'])
    @app.route('/dashboard/', defaults={'subpath': ''}, methods=['GET'])
    @app.route('/dashboard/<path:subpath>', methods=['GET'])
    def serve_dashboard(subpath=''):
        return serve_spa()

    @app.route('/', defaults={'path': ''}, methods=['GET'])
    @app.route('/<path:path>', methods=['GET'])
    def serve_frontend(path=''):
        """Catch-all for frontend routes - only handles GET"""
        if path.startswith('api/'):
            return jsonify({'message': 'Endpoint not found', 'status': 404}), 404

        return serve_spa(path)

    return app


app = create_app()

