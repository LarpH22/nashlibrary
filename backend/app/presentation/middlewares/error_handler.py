import os
from flask import jsonify, current_app, request, send_from_directory
from flask_jwt_extended.exceptions import JWTExtendedException
import traceback
import sys


def register_error_handlers(app):
    """Register error handlers for common HTTP and application errors."""
    
    @app.errorhandler(404)
    def not_found(error):
        path = request.path or ''
        if request.method == 'GET' and not path.startswith('/api/'):
            frontend_dist = current_app.config.get('FRONTEND_DIST_FOLDER')
            if frontend_dist:
                index_path = os.path.join(frontend_dist, 'index.html')
                if os.path.exists(index_path):
                    return send_from_directory(frontend_dist, 'index.html')
        return jsonify({'message': 'Endpoint not found', 'status': 404}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'message': 'Method not allowed',
            'status': 405,
            'valid_methods': getattr(error, 'valid_methods', None)
        }), 405

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'message': 'Bad request', 'status': 400}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'message': 'Unauthorized access', 'status': 401}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'message': 'Forbidden', 'status': 403}), 403

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Internal server error: {str(error)}')
        return jsonify({'message': 'Internal server error', 'status': 500}), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        # Log the exception with full traceback
        error_msg = f'Unhandled exception: {type(e).__name__}: {str(e)}'
        app.logger.error(error_msg, exc_info=True)
        
        # Also print to stderr for debugging
        print(f'\n[ERROR] {error_msg}', file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        
        # Special handling for JWT exceptions
        if isinstance(e, JWTExtendedException):
            return jsonify({'message': str(e), 'status': 401}), 401
        
        # Return error with more info in development
        error_response = {
            'message': 'Internal server error',
            'status': 500
        }
        
        # Add error details in development mode
        if current_app.debug or current_app.config.get('ENV') == 'development':
            error_response['error'] = {
                'type': type(e).__name__,
                'message': str(e)
            }
        
        return jsonify(error_response), 500
