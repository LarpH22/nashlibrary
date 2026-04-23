# Test Accounts

This folder contains information about all test accounts available in the Nash Library system.

## Admin Account

**Role:** Administrator  
**Email:** `admin@library.com`  
**Password:** `admin123`  

**Permissions:** Full system access, can manage users, librarians, students, and view reports.

---

## User Accounts (Staff/Manager)

### User 1 (Senior)

**Role:** Senior User  
**Email:** `librarian1@library.com`  
**Password:** `librarian123`  
**Employee ID:** `LIB001`  
**Position:** Senior User  

**Permissions:** 
- Borrow/return books
- Add new books
- Manage fines
- View reports

### User 2 (Junior)

**Role:** Junior User  
**Email:** `librarian2@library.com`  
**Password:** `librarian123`  
**Employee ID:** `LIB002`  
**Position:** Junior User  

**Permissions:**
- Borrow/return books
- View book catalog
- Limited fine management

### User 3 (General)

**Role:** User  
**Email:** `user1@library.com`  
**Password:** `user123`  

**Permissions:**
- Browse the book catalog
- View available books
- Search for titles and authors
- View own profile and borrowing history

---

## Student Accounts

### Student 1

**Role:** Student  
**Email:** `tsudent1@library.com`  
**Password:** `student123`  
**Student Number:** `STU2024001`  
**Department:** Computer Science  
**Year Level:** 3  

**Features:**
- Search and borrow books
- View borrowed books
- Check due dates and fines

### Student 2

**Role:** Student  
**Email:** `student2@library.com`  
**Password:** `student123`  
**Student Number:** `STU2024002`  
**Department:** Information Technology  
**Year Level:** 2  

**Features:**
- Search and borrow books
- View borrowed books
- Check due dates and fines

---

## How to Use

1. Start the Flask backend:
   ```bash
   python backend/app.py
   ```

2. Open the frontend in your browser:
   ```
   http://localhost:5000
   ```

3. Click **Sign In** and use any of the credentials above

4. Select your role and login to test the system

---

## Notes

- All test accounts are pre-configured in the database
- Passwords are hashed and secure
- To reset test data, run:
  ```bash
  python create_test_users.py
  ```

- Test accounts have access to demo books and features

---

## API Testing

You can also test the API directly using `curl` or Postman:

```bash
# Login as Admin
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin@library.com", "password": "admin123"}'

# Login as Student
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "student1@library.com", "password": "student123"}'
```

---

**Last Updated:** April 10, 2026
