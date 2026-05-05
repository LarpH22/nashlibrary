import os
from dotenv import load_dotenv

# Load .env automatically for local development
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '.env'), override=True)
load_dotenv(os.path.join(basedir, '.env'), override=True)
load_dotenv(override=True)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'

    # Database configuration
    USE_MYSQL = os.environ.get('USE_MYSQL', 'true').lower() == 'true'

    DB_HOST = os.environ.get('DB_HOST') or '127.0.0.1'
    DB_PORT = int(os.environ.get('DB_PORT', '3307'))
    DB_USER = os.environ.get('DB_USER') or 'root'
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME') or 'library_system_v2'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'

    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@library.com'

    # Backend and frontend URLs for email links and redirects
    BACKEND_URL = os.environ.get('BACKEND_URL') or 'http://127.0.0.1:5000'
    _USE_DEV_FRONTEND = os.environ.get('USE_DEV_FRONTEND', 'false').lower() in ['true', '1', 'yes']
    _configured_frontend_url = os.environ.get('FRONTEND_URL')

    if _USE_DEV_FRONTEND:
        FRONTEND_URL = _configured_frontend_url or 'http://127.0.0.1:3000'
    else:
        # When not using the Vite dev frontend, prefer the backend host for generated links.
        FRONTEND_URL = _configured_frontend_url or BACKEND_URL
        if _configured_frontend_url and _configured_frontend_url.startswith(('http://localhost:3000', 'https://localhost:3000', 'http://127.0.0.1:3000', 'https://127.0.0.1:3000')):
            FRONTEND_URL = BACKEND_URL

    # Frontend dist folder for serving built static files
    FRONTEND_DIST_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist')

    # File upload configuration
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 25 * 1024 * 1024))
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    EBOOK_UPLOAD_FOLDER = os.environ.get(
        'EBOOK_UPLOAD_FOLDER',
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'ebooks')
    )
    QR_CODE_FOLDER = os.environ.get(
        'QR_CODE_FOLDER',
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'qr_codes')
    )
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
    ALLOWED_EBOOK_EXTENSIONS = {'pdf', 'epub'}
