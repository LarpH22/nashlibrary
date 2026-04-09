# NashLibrary - Online Library Management System

This project consists of a Flask backend with MySQL database and a React frontend for user login, registration, and role-based dashboards.

## Prerequisites

- Python 3.8+
- Node.js 16+
- MySQL Server 8.0+

## Backend (Flask + MySQL)

The backend is located in the `backend/` directory.

### Setup

1. **Install MySQL Server** (see MYSQL_SETUP.md for detailed instructions)

2. Navigate to the backend directory:
   ```bash
   cd backend
   ```

3. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Setup MySQL database:
   ```bash
   python setup_mysql.py
   ```

6. Create test accounts:
   ```bash
   python create_test_accounts.py
   ```

7. Run the backend:
   ```bash
   python app.py
   ```

## Frontend (React + Vite)

The frontend is located in the `frontend/` directory.

### Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Build for production:
   ```bash
   npm run build
   ```

## Usage

1. Start the backend server (serves both API and frontend)
2. Open browser to `http://localhost:5000`
3. Click "Get Started" to login or register
4. Use test accounts:
   - **Student**: username: `student1`, password: `pass123`
   - **Librarian**: username: `librarian1`, password: `pass123`
   - **Admin**: username: `admin1`, password: `pass123`

## Features

- User registration and authentication
- Role-based access control (Admin, Librarian, Student, User)
- JWT token-based sessions
- Responsive React frontend
- MySQL database with SQLAlchemy ORM

## API Endpoints

- `POST /register` - User registration
- `POST /login` - User login
- `GET /user` - Get current user info (protected)
- `GET /protected` - Test protected route

## Database Schema

- **User Table**: id, username, email, password_hash, role

## Development

- Backend runs on `http://localhost:5000`
- Frontend dev server: `npm run dev` (port 5173)
- Database: MySQL with PyMySQL connector

3. Run the Flask app:
   ```
   python app.py
   ```

The backend will run on `http://localhost:5000` and serve the built frontend at the same address (no separate dev server needed after build).

## Frontend (React)

The frontend is located in the `frontend/` directory.

### Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Run the development server:
   ```
   npm run dev
   ```

The frontend will run on `http://localhost:5173` (default Vite port).

## Usage

- Open the frontend in your browser.
- Use the form to register a new user or login with existing credentials.
- The backend handles user authentication and stores data in a SQLite database.

## API Endpoints

- `POST /register`: Register a new user (username, email, password)
- `POST /login`: Login and get JWT token (username, password)
- `GET /protected`: Access protected route (requires JWT token)