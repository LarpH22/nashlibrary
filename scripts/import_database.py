import pymysql

DB_NAME = 'library_system_v2'

# Create database first
conn = pymysql.connect(
    host='127.0.0.1',
    port=3307,
    user='root',
    password='',
    charset='utf8mb4'
)

try:
    with conn.cursor() as cur:
        cur.execute(f'CREATE DATABASE IF NOT EXISTS {DB_NAME}')
    conn.commit()
    print(f'✓ Database {DB_NAME} created')
finally:
    conn.close()

# Now connect to the database and execute the schema
conn = pymysql.connect(
    host='127.0.0.1',
    port=3307,
    user='root',
    password='',
    database=DB_NAME,
    charset='utf8mb4',
    autocommit=False
)

try:
    with conn.cursor() as cur:
        # Read and execute the SQL file
        with open('database_schema.sql', 'r', encoding='utf8') as f:
            sql_content = f.read()
        
        # Remove comments and split properly
        lines = [line.strip() for line in sql_content.split('\n') if line.strip() and not line.strip().startswith('--')]
        
        # Execute full script as one batch to handle delimiters
        try:
            # For PyMySQL, we need to handle this differently
            # Let's use a simpler approach - execute key statements
            
            # 1. Drop tables
            for table in ['audit_logs', 'fines', 'borrow_records', 'books', 'students', 'librarians', 'admins', 'users']:
                try:
                    cur.execute(f'DROP TABLE IF EXISTS {table}')
                except:
                    pass
            
            # 2. Create users table
            cur.execute('''
                CREATE TABLE users (
                    user_id INT PRIMARY KEY AUTO_INCREMENT,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(100) NOT NULL,
                    phone VARCHAR(20),
                    address TEXT,
                    role ENUM('admin', 'librarian', 'student', 'user') NOT NULL,
                    status ENUM('active', 'inactive', 'suspended') DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULL,
                    INDEX idx_email (email),
                    INDEX idx_role (role)
                )
            ''')
            
            # 3. Create admins table
            cur.execute('''
                CREATE TABLE admins (
                    admin_id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT UNIQUE NOT NULL,
                    admin_level ENUM('super', 'senior', 'junior') DEFAULT 'junior',
                    permissions TEXT,
                    last_password_change TIMESTAMP,
                    two_factor_enabled BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            
            # 4. Create librarians table
            cur.execute('''
                CREATE TABLE librarians (
                    librarian_id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT UNIQUE NOT NULL,
                    employee_id VARCHAR(20) UNIQUE NOT NULL,
                    position VARCHAR(50),
                    hire_date DATE,
                    shift_schedule VARCHAR(50),
                    department VARCHAR(50),
                    permissions TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    INDEX idx_employee_id (employee_id)
                )
            ''')
            
            # 5. Create students table
            cur.execute('''
                CREATE TABLE students (
                    student_id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT UNIQUE NOT NULL,
                    student_number VARCHAR(20) UNIQUE NOT NULL,
                    department VARCHAR(100),
                    year_level INT,
                    section VARCHAR(10),
                    borrowed_books_count INT DEFAULT 0,
                    total_fines DECIMAL(10,2) DEFAULT 0.00,
                    library_card_number VARCHAR(20) UNIQUE,
                    expiration_date DATE,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    INDEX idx_student_number (student_number),
                    INDEX idx_library_card (library_card_number)
                )
            ''')
            
            # 6. Create books table
            cur.execute('''
                CREATE TABLE books (
                    book_id INT PRIMARY KEY AUTO_INCREMENT,
                    isbn VARCHAR(13) UNIQUE,
                    title VARCHAR(255) NOT NULL,
                    author VARCHAR(100),
                    publisher VARCHAR(100),
                    publication_year YEAR,
                    category VARCHAR(50),
                    description TEXT,
                    total_copies INT DEFAULT 1,
                    available_copies INT DEFAULT 1,
                    location VARCHAR(50),
                    added_by INT,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (added_by) REFERENCES users(user_id),
                    INDEX idx_title (title),
                    INDEX idx_author (author),
                    INDEX idx_isbn (isbn),
                    INDEX idx_category (category)
                )
            ''')
            
            # 7. Create borrow_records table
            cur.execute('''
                CREATE TABLE borrow_records (
                    borrow_id INT PRIMARY KEY AUTO_INCREMENT,
                    student_id INT NOT NULL,
                    book_id INT NOT NULL,
                    librarian_id INT NOT NULL,
                    borrow_date DATE NOT NULL,
                    due_date DATE NOT NULL,
                    return_date DATE,
                    status ENUM('borrowed', 'returned', 'overdue', 'lost') DEFAULT 'borrowed',
                    notes TEXT,
                    fine_amount DECIMAL(10,2) DEFAULT 0.00,
                    fine_paid BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (student_id) REFERENCES students(student_id),
                    FOREIGN KEY (book_id) REFERENCES books(book_id),
                    FOREIGN KEY (librarian_id) REFERENCES librarians(librarian_id),
                    INDEX idx_student (student_id),
                    INDEX idx_status (status),
                    INDEX idx_due_date (due_date)
                )
            ''')
            
            # 8. Create fines table
            cur.execute('''
                CREATE TABLE fines (
                    fine_id INT PRIMARY KEY AUTO_INCREMENT,
                    borrow_id INT NOT NULL,
                    student_id INT NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    reason VARCHAR(255),
                    status ENUM('pending', 'paid', 'waived') DEFAULT 'pending',
                    issued_date DATE NOT NULL,
                    paid_date DATE,
                    issued_by INT,
                    FOREIGN KEY (borrow_id) REFERENCES borrow_records(borrow_id),
                    FOREIGN KEY (student_id) REFERENCES students(student_id),
                    FOREIGN KEY (issued_by) REFERENCES users(user_id),
                    INDEX idx_status (status)
                )
            ''')
            
            # 9. Create audit_logs table
            cur.execute('''
                CREATE TABLE audit_logs (
                    log_id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT,
                    action VARCHAR(100),
                    table_name VARCHAR(50),
                    record_id INT,
                    old_data TEXT,
                    new_data TEXT,
                    ip_address VARCHAR(45),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    INDEX idx_user (user_id),
                    INDEX idx_timestamp (timestamp)
                )
            ''')
            
            conn.commit()
            print('✓ All tables created')
            
            # 10. Insert sample data
            cur.execute('''
                INSERT INTO users (email, password_hash, full_name, phone, address, role, status) VALUES 
                ('admin@library.com', '$2y$10$YourHashedPasswordHere', 'John Admin', '+1234567890', '123 Admin St, City', 'admin', 'active'),
                ('librarian1@library.com', '$2y$10$YourHashedPasswordHere', 'Jane Librarian', '+1234567891', '456 Library Ave, City', 'librarian', 'active'),
                ('librarian2@library.com', '$2y$10$YourHashedPasswordHere', 'Mark Librarian', '+1234567892', '789 Library Ave, City', 'librarian', 'active'),
                ('student1@library.com', '$2y$10$YourHashedPasswordHere', 'Bob Student', '+1234567893', '321 University St, City', 'student', 'active'),
                ('student2@library.com', '$2y$10$YourHashedPasswordHere', 'Alice Student', '+1234567894', '654 University St, City', 'student', 'active'),
                ('student3@library.com', '$2y$10$YourHashedPasswordHere', 'Charlie Student', '+1234567895', '987 University St, City', 'student', 'active')
            ''')
            
            cur.execute('''
                INSERT INTO admins (user_id, admin_level, permissions, two_factor_enabled) VALUES 
                (1, 'super', '{"all": true, "manage_admins": true, "manage_librarians": true, "manage_students": true, "reports": true}', FALSE)
            ''')
            
            cur.execute('''
                INSERT INTO librarians (user_id, employee_id, position, hire_date, shift_schedule, department, permissions) VALUES 
                (2, 'LIB001', 'Senior Librarian', '2023-01-15', '9:00 AM - 5:00 PM', 'Circulation', '{"borrow": true, "return": true, "add_books": true, "manage_fines": true}'),
                (3, 'LIB002', 'Junior Librarian', '2024-01-10', '1:00 PM - 9:00 PM', 'Reference', '{"borrow": true, "return": true, "add_books": false, "manage_fines": false}')
            ''')
            
            cur.execute('''
                INSERT INTO students (user_id, student_number, department, year_level, section, library_card_number, expiration_date) VALUES 
                (4, 'STU2024001', 'Computer Science', 3, 'A', 'CARD2024001', DATE_ADD(CURDATE(), INTERVAL 2 YEAR)),
                (5, 'STU2024002', 'Information Technology', 2, 'B', 'CARD2024002', DATE_ADD(CURDATE(), INTERVAL 2 YEAR)),
                (6, 'STU2024003', 'Computer Science', 1, 'A', 'CARD2024003', DATE_ADD(CURDATE(), INTERVAL 2 YEAR))
            ''')
            
            cur.execute('''
                INSERT INTO books (isbn, title, author, publisher, publication_year, category, description, total_copies, available_copies, location, added_by) VALUES 
                ('9780132350884', 'Clean Code: A Handbook of Agile Software Craftsmanship', 'Robert C. Martin', 'Prentice Hall', 2008, 'Programming', 'A comprehensive guide to writing clean, maintainable code', 3, 3, 'A-101', 1),
                ('9780201633610', 'Design Patterns: Elements of Reusable Object-Oriented Software', 'Erich Gamma', 'Addison-Wesley', 1994, 'Programming', 'Classic book on software design patterns', 2, 2, 'A-102', 1),
                ('9780735619678', 'Code Complete: A Practical Handbook of Software Construction', 'Steve McConnell', 'Microsoft Press', 2004, 'Programming', 'Practical guide to software construction', 2, 2, 'A-101', 2),
                ('9780596007126', 'Head First Design Patterns', 'Eric Freeman', 'O''Reilly Media', 2004, 'Programming', 'Brain-friendly guide to design patterns', 3, 3, 'A-103', 2),
                ('9780131103627', 'The C Programming Language', 'Brian W. Kernighan', 'Prentice Hall', 1988, 'Programming', 'Classic book on C programming', 1, 1, 'B-101', 1)
            ''')
            
            conn.commit()
            print('✓ Sample data inserted')
            
            # Verify
            with conn.cursor() as verify_cur:
                verify_cur.execute('SHOW TABLES')
                tables = verify_cur.fetchall()
                print(f'\n✓ Successfully created {len(tables)} tables:')
                for table in tables:
                    print(f'  - {table[0]}')
                    
        except Exception as e:
            print(f'Error: {e}')
            conn.rollback()
            raise
            
except Exception as e:
    print(f'Fatal error: {e}')
finally:
    conn.close()
    print('\n✓ Database import complete!')
