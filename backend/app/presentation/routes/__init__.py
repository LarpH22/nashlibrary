from .root_routes import root_bp
from .auth_routes import auth_bp
from .user_routes import user_bp
from .book_routes import book_bp
from .fine_routes import fine_bp
from .admin_routes import admin_bp


def register_blueprints(app):
    """Register all route blueprints with the Flask app."""
    print("Registering blueprints")
    # Root routes (health check, etc.)
    app.register_blueprint(root_bp)
    # Auth routes: /api/auth/login, /api/auth/register, /api/auth/profile
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    print("Auth blueprint registered at /api/auth")
    # User routes: /users/*, /profile
    app.register_blueprint(user_bp, url_prefix='/users')
    # Admin routes: /api/admin/*
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    # Book routes: /books/*
    app.register_blueprint(book_bp, url_prefix='/books')
    # Fine routes: /fines/*
    app.register_blueprint(fine_bp, url_prefix='/fines')
