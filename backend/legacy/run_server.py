#!/usr/bin/env python
import os
import sys
sys.path.insert(0, 'backend')

os.environ.setdefault('DB_PORT', '3307')

from backend.app import app

# Enable debug to see errors
if __name__ == '__main__':
    print("Starting Flask app on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=False)
