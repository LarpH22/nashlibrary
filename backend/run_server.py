import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, PARENT_DIR)

from backend.app import app

if __name__ == '__main__':
    print('Starting NashLibrary backend on http://127.0.0.1:5000')
    app.run(host='127.0.0.1', port=5000, debug=False)
