import os
import sys
import logging
from logging import FileHandler, Formatter

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, PARENT_DIR)

# Prefer serving the built frontend from the same backend port by default.
os.environ.setdefault('USE_DEV_FRONTEND', 'false')
os.environ.setdefault('FLASK_ENV', 'production')

from backend.app import app
from backend.config import Config

def env_flag(name, default='false'):
    return os.environ.get(name, default).lower() in {'true', '1', 'yes', 'on'}


debug_enabled = env_flag('FLASK_DEBUG')
log_level = logging.DEBUG if debug_enabled else logging.INFO

# Configure logging without forcing debug mode in normal runs.
logging.basicConfig(level=log_level, stream=sys.stderr)
app.logger.setLevel(log_level)
logging.getLogger('werkzeug').setLevel(log_level)

log_file = os.path.join(CURRENT_DIR, 'backend.log')
file_handler = FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(log_level)
file_handler.setFormatter(Formatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
logging.getLogger().addHandler(file_handler)
app.logger.addHandler(file_handler)

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', '5000'))
    print(f'Starting LIBRASYS backend on {Config.BACKEND_URL}')
    print(f'Listening on {host}:{port}')
    print(f'USE_DEV_FRONTEND={os.environ.get("USE_DEV_FRONTEND")}')
    print(f'FRONTEND_URL={Config.FRONTEND_URL}')
    print(f'DB_HOST={Config.DB_HOST} DB_PORT={Config.DB_PORT} DB_NAME={Config.DB_NAME}')
    print(f'FLASK_DEBUG={debug_enabled}')
    app.run(host=host, port=port, debug=debug_enabled)
