import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, PARENT_DIR)

# Prefer serving the built frontend from the same backend port by default.
os.environ.setdefault('USE_DEV_FRONTEND', 'false')
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import app

if __name__ == '__main__':
    print('Starting NashLibrary backend on http://127.0.0.1:5000')
    print(f'USE_DEV_FRONTEND={os.environ.get("USE_DEV_FRONTEND")}')
    print(f'FRONTEND_URL={os.environ.get("FRONTEND_URL", "http://localhost:3000")}')
    app.run(host='127.0.0.1', port=5000, debug=False)
