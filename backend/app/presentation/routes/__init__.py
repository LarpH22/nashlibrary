from .root_routes import root_bp
from .auth_routes import auth_bp
from .user_routes import user_bp
from .student_routes import student_bp
from .loan_routes import loan_bp
from .book_routes import book_bp
from .book_search_routes import book_search_bp
from .fine_routes import fine_bp
from .admin_routes import admin_bp
from .seed_routes import seed_bp
from .reminder_routes import reminder_bp


def register_blueprints(app):
    """Register all route blueprints with the Flask app."""
    # Root routes (health check, etc.)
    app.register_blueprint(root_bp)
    # Auth routes: /api/auth/login, /api/auth/register, /api/auth/profile
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    # Student routes: /api/students/profile and /api/student/profile
    app.register_blueprint(student_bp, url_prefix='/api/students')
    app.register_blueprint(student_bp, url_prefix='/api/student', name='student_singular')
    # Loan routes: /api/loans/student
    app.register_blueprint(loan_bp, url_prefix='/api/loans')
    # User routes: /users/*, /profile
    app.register_blueprint(user_bp, url_prefix='/users')
    # Admin routes: /api/admin/*
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    # Seed routes: /api/seed/books
    app.register_blueprint(seed_bp, url_prefix='/api/seed')
    # Book routes: /books/*
    app.register_blueprint(book_bp, url_prefix='/books')
    # Search books: /api/books/search
    app.register_blueprint(book_search_bp, url_prefix='/api/books')
    # Fine routes: /fines/*
    app.register_blueprint(fine_bp, url_prefix='/fines')
    # Reminder routes: /reminders/*
    app.register_blueprint(reminder_bp, url_prefix='/api/reminders')
