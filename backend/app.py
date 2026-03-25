import os
import subprocess
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from sqlalchemy import or_
from models import db, User
from config import Config

import re

EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def validate_registration(username, email, password):
    if not username or not email or not password:
        return 'Username, email, and password are required.'
    if len(username.strip()) < 3:
        return 'Username must be at least 3 characters long.'
    if not EMAIL_REGEX.match(email):
        return 'Enter a valid email address.'
    if len(password) < 6:
        return 'Password must be at least 6 characters long.'
    if ' ' in password:
        return 'Password must not contain spaces.'
    return None


def validate_login(username, password):
    if not username or not password:
        return 'Username/email and password are required.'
    if len(username.strip()) < 3:
        return 'Please supply a valid username or email.'
    if len(password) < 6:
        return 'Password must be at least 6 characters long.'
    return None

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
frontend_build_dir = os.path.join(frontend_dir, 'dist')

def build_frontend():
    index_html = os.path.join(frontend_build_dir, 'index.html')
    if os.path.exists(index_html):
        return

    npm_command = 'npm'
    if os.name == 'nt':
        npm_command = 'npm.cmd'

    try:
        subprocess.run([npm_command, 'install'], cwd=frontend_dir, check=True)
        subprocess.run([npm_command, 'run', 'build'], cwd=frontend_dir, check=True)
    except FileNotFoundError:
        raise RuntimeError(
            'npm is not installed or not found in PATH. ' 
            'Install Node.js and npm, then run `npm install` and `npm run build` in the frontend folder.'
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f'Frontend build failed (command={exc.cmd}, returncode={exc.returncode}). ' 
            'Run `npm install` and `npm run build` manually to inspect errors.'
        )

build_frontend()

app = Flask(__name__, static_folder=frontend_build_dir, static_url_path='')
app.config.from_object(Config)

db.init_app(app)
jwt = JWTManager(app)
CORS(app)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    if path != '' and os.path.exists(os.path.join(app.static_folder, path)):
        return app.send_static_file(path)
    return app.send_static_file('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    validation_error = validate_registration(username, email, password)
    if validation_error:
        return jsonify({'message': validation_error}), 400

    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return jsonify({'message': 'User already exists with this username or email'}), 400

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    validation_error = validate_login(username, password)
    if validation_error:
        return jsonify({'message': validation_error}), 400

    user = User.query.filter(or_(User.username == username, User.email == username)).first()
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.username)
        return jsonify({'access_token': access_token, 'message': 'Logged in successfully'}), 200

    return jsonify({'message': 'Invalid username/email or password'}), 401

@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({'message': f'Hello, {current_user}!'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)