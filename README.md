# Login and Registration System

This project consists of a Flask backend and a React frontend for user login and registration.

## Backend (Flask)

The backend is located in the `backend/` directory.

### Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

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