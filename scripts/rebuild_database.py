import pymysql
from werkzeug.security import generate_password_hash

# Connection to create database
conn = pymysql.connect(
    host='127.0.0.1',
    port=3307,
    user='root',
    password='',
    charset='utf8mb4'
)

try:
    with conn.cursor() as cur:
        # Drop and recreate database
        print("Dropping existing database...")
        cur.execute('DROP DATABASE IF EXISTS library_system_v2')
        conn.commit()
        
        print("Creating database...")
        cur.execute('CREATE DATABASE library_system_v2 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
        conn.commit()
        
    conn.close()
    
    # Reconnect to new database
    conn = pymysql.connect(
        host='127.0.0.1',
        port=3307,
        user='root',
        password='',
        database='library_system_v2',
        charset='utf8mb4'
    )
    
    with conn.cursor() as cur:
        print("Creating tables...")
        
        # ADMINS TABLE
        cur.execute('''
        CREATE TABLE admins (
            admin_id INT PRIMARY KEY AUTO_INCREMENT,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            phone VARCHAR(20),
            address TEXT,
            admin_level ENUM('super', 'senior', 'junior') DEFAULT 'junior',
            permissions JSON,
            status ENUM('active', 'inactive', 'suspended') DEFAULT 'active',
            last_password_change TIMESTAMP,
            two_factor_enabled BOOLEAN DEFAULT FALSE,
            last_login TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_email (email),
            INDEX idx_status (status)
        )
        ''')
        
        # LIBRARIANS TABLE
        cur.execute('''
        CREATE TABLE librarians (
            librarian_id INT PRIMARY KEY AUTO_INCREMENT,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            employee_id VARCHAR(50),
            phone VARCHAR(20),
            address TEXT,
            position VARCHAR(100),
            department VARCHAR(30),
            status ENUM('active', 'inactive', 'suspended') DEFAULT 'active',
            last_password_change TIMESTAMP,
            two_factor_enabled BOOLEAN DEFAULT FALSE,
            last_login TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_email (email),
            INDEX idx_employee_id (employee_id),
            INDEX idx_status (status)
        )
        ''')
        
        # STUDENTS TABLE
        cur.execute('''
        CREATE TABLE students (
            student_id INT PRIMARY KEY AUTO_INCREMENT,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            student_number VARCHAR(20),
            phone VARCHAR(20),
            address TEXT,
            department VARCHAR(30),
            year_level INT,
            section VARCHAR(10),
            borrowed_books_count INT DEFAULT 0,
            total_fines DECIMAL(10, 2) DEFAULT 0.00,
            library_card_number VARCHAR(20),
            expiration_date DATE,
            registration_document VARCHAR(255),
            is_verified BOOLEAN DEFAULT FALSE,
            status ENUM('pending', 'active', 'inactive', 'suspended', 'rejected') DEFAULT 'pending',
            email_verified BOOLEAN DEFAULT FALSE,
            verification_token VARCHAR(255),
            reset_token VARCHAR(255),
            reset_expires_at TIMESTAMP NULL,
            proof_file VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_email (email),
            INDEX idx_student_number (student_number),
            INDEX idx_status (status)
        )
        ''')
        
        # REGISTRATION_REQUESTS TABLE
        cur.execute('''
        CREATE TABLE registration_requests (
            request_id INT PRIMARY KEY AUTO_INCREMENT,
            email VARCHAR(100) UNIQUE NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            student_number VARCHAR(20),
            role ENUM('student', 'librarian', 'admin') NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            registration_document VARCHAR(255),
            verification_token VARCHAR(255),
            email_verified BOOLEAN DEFAULT FALSE,
            verified_at TIMESTAMP NULL,
            status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_email (email),
            INDEX idx_status (status),
            INDEX idx_verification_token (verification_token)
        )
        ''' )
        
        # BOOKS TABLE
        cur.execute('''
        CREATE TABLE books (
            book_id INT PRIMARY KEY AUTO_INCREMENT,
            title VARCHAR(200) NOT NULL,
            isbn VARCHAR(20) UNIQUE,
            status ENUM('available', 'borrowed', 'damaged', 'lost', 'maintenance') DEFAULT 'available',
            location VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_title (title),
            INDEX idx_isbn (isbn),
            INDEX idx_status (status)
        )
        ''')
        
        # BORROW_RECORDS TABLE
        cur.execute('''
        CREATE TABLE borrow_records (
            borrow_id INT PRIMARY KEY AUTO_INCREMENT,
            student_id INT NOT NULL,
            book_id INT NOT NULL,
            borrow_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date DATE NOT NULL,
            return_date DATE,
            status ENUM('active', 'returned', 'overdue') DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
            FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
            INDEX idx_student_id (student_id),
            INDEX idx_book_id (book_id),
            INDEX idx_status (status)
        )
        ''')
        
        # FINES TABLE
        cur.execute('''
        CREATE TABLE fines (
            fine_id INT PRIMARY KEY AUTO_INCREMENT,
            borrow_id INT NOT NULL,
            student_id INT NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            reason VARCHAR(255),
            status ENUM('unpaid', 'paid', 'waived') DEFAULT 'unpaid',
            issued_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            paid_date TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (borrow_id) REFERENCES borrow_records(borrow_id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
            INDEX idx_student_id (student_id),
            INDEX idx_status (status)
        )
        ''')
        
        # AUDIT_LOGS TABLE
        cur.execute('''
        CREATE TABLE audit_logs (
            log_id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT,
            user_role ENUM('admin', 'librarian', 'student') NOT NULL,
            action VARCHAR(255) NOT NULL,
            entity_type VARCHAR(100),
            entity_id INT,
            old_values JSON,
            new_values JSON,
            ip_address VARCHAR(45),
            user_agent VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            INDEX idx_user_role (user_role),
            INDEX idx_action (action),
            INDEX idx_created_at (created_at)
        )
        ''')
        
        conn.commit()
        print("Tables created successfully!")
        
        # Insert test data
        print("\nInserting test data...")
        
        # Test admin
        admin_hash = generate_password_hash('admin123', method='pbkdf2:sha256')
        cur.execute('''
            INSERT INTO admins (email, password_hash, full_name, admin_level, status)
            VALUES (%s, %s, %s, %s, %s)
        ''', ('admin@library.com', admin_hash, 'John Admin', 'super', 'active'))
        
        # Test librarians
        librarian_hash = generate_password_hash('librarian123', method='pbkdf2:sha256')
        cur.execute('''
            INSERT INTO librarians (email, password_hash, full_name, employee_id, position, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', ('librarian1@library.com', librarian_hash, 'Alice Librarian', 'LIB001', 'Senior Librarian', 'active'))
        
        cur.execute('''
            INSERT INTO librarians (email, password_hash, full_name, employee_id, position, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', ('librarian2@library.com', librarian_hash, 'Bob Librarian', 'LIB002', 'Junior Librarian', 'active'))
        
        # Test students
        student_hash = generate_password_hash('student123', method='pbkdf2:sha256')
        cur.execute('''
            INSERT INTO students (email, password_hash, full_name, student_number, status, email_verified)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', ('student1@library.com', student_hash, 'Charlie Student', 'STU001', 'active', True))
        
        cur.execute('''
            INSERT INTO students (email, password_hash, full_name, student_number, status, email_verified)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', ('student2@library.com', student_hash, 'Diana Student', 'STU002', 'active', True))
        
        # Test books
        cur.execute('''
            INSERT INTO books (title, isbn, status, location)
            VALUES (%s, %s, %s, %s)
        ''', ('Python Programming', '978-0-13-110362-7', 'available', 'Shelf A1'))
        
        cur.execute('''
            INSERT INTO books (title, isbn, status, location)
            VALUES (%s, %s, %s, %s)
        ''', ('Clean Code', '978-0-13-235088-4', 'available', 'Shelf B2'))
        
        conn.commit()
        print("Test data inserted successfully!")
        
finally:
    conn.close()
