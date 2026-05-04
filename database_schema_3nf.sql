-- =====================================================
-- ONLINE LIBRARY MANAGEMENT SYSTEM - 3NF NORMALIZED SCHEMA
-- =====================================================
-- This schema is normalized to 3NF with:
-- - Separate dimension tables (authors, categories)
-- - No redundant fields
-- - Dynamic availability computation
-- - Clean foreign key relationships
-- - Proper constraints and indices
-- =====================================================

-- Drop existing tables (in correct order to avoid foreign key constraints)
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS fines;
DROP TABLE IF EXISTS borrow_records;
DROP TABLE IF EXISTS books_categories;
DROP TABLE IF EXISTS book_authors;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS authors;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS registration_requests;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS librarians;
DROP TABLE IF EXISTS admins;

-- =====================================================
-- 1. ADMINS TABLE (Admin-specific details - independent table with auth)
-- =====================================================
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
);

-- =====================================================
-- 2. LIBRARIANS TABLE (Librarian-specific details - independent table with auth)
-- =====================================================
CREATE TABLE librarians (
    librarian_id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    employee_id VARCHAR(20) UNIQUE NOT NULL,
    position VARCHAR(50),
    hire_date DATE,
    phone VARCHAR(20),
    address TEXT,
    shift_schedule VARCHAR(50),
    department VARCHAR(50),
    permissions JSON,
    status ENUM('active', 'inactive', 'suspended') DEFAULT 'active',
    last_login TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_employee_id (employee_id),
    INDEX idx_status (status)
);

-- =====================================================
-- 3. STUDENTS TABLE (Student-specific details - independent table with auth)
-- =====================================================
CREATE TABLE students (
    student_id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    student_number VARCHAR(20) UNIQUE NOT NULL,
    department VARCHAR(100),
    year_level INT,
    section VARCHAR(10),
    registration_document VARCHAR(255),
    status ENUM('active', 'inactive', 'suspended', 'pending') DEFAULT 'pending',
    email_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255),
    reset_token VARCHAR(255),
    reset_expires_at TIMESTAMP NULL,
    last_login TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_student_number (student_number),
    INDEX idx_status (status)
);

-- =====================================================
-- 4. REGISTRATION REQUESTS TABLE
-- =====================================================
CREATE TABLE registration_requests (
    request_id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    student_number VARCHAR(20) UNIQUE NOT NULL,
    department VARCHAR(100) NOT NULL,
    year_level INT NOT NULL,
    registration_document VARCHAR(255),
    role ENUM('admin', 'librarian', 'student') DEFAULT 'student',
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    verification_token VARCHAR(255),
    email_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_student_number (student_number),
    INDEX idx_verification_token (verification_token)
);

-- =====================================================
-- 6. AUTHORS TABLE (Normalized - separate dimension)
-- =====================================================
CREATE TABLE authors (
    author_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name)
);

-- =====================================================
-- 7. CATEGORIES TABLE (Normalized - separate dimension)
-- =====================================================
CREATE TABLE categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name)
);

-- =====================================================
-- 8. BOOKS TABLE (Normalized - no redundant fields)
-- =====================================================
CREATE TABLE books (
    book_id INT PRIMARY KEY AUTO_INCREMENT,
    isbn VARCHAR(13) UNIQUE,
    title VARCHAR(255) NOT NULL,
    publisher VARCHAR(100),
    publication_year YEAR,
    description TEXT,
    total_copies INT DEFAULT 1 CHECK (total_copies > 0),
    location VARCHAR(50),
    added_by INT,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (added_by) REFERENCES librarians(librarian_id),
    INDEX idx_title (title),
    INDEX idx_isbn (isbn),
    INDEX idx_location (location)
);

-- =====================================================
-- 9. BOOK_AUTHORS TABLE (Many-to-Many relationship)
-- =====================================================
CREATE TABLE book_authors (
    book_author_id INT PRIMARY KEY AUTO_INCREMENT,
    book_id INT NOT NULL,
    author_id INT NOT NULL,
    author_order INT DEFAULT 1,
    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES authors(author_id) ON DELETE CASCADE,
    UNIQUE KEY unique_book_author (book_id, author_id),
    INDEX idx_book_id (book_id),
    INDEX idx_author_id (author_id)
);

-- =====================================================
-- 10. BOOKS_CATEGORIES TABLE (Many-to-Many relationship)
-- =====================================================
CREATE TABLE books_categories (
    book_category_id INT PRIMARY KEY AUTO_INCREMENT,
    book_id INT NOT NULL,
    category_id INT NOT NULL,
    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE,
    UNIQUE KEY unique_book_category (book_id, category_id),
    INDEX idx_book_id (book_id),
    INDEX idx_category_id (category_id)
);

-- =====================================================
-- 11. BORROWING RECORDS TABLE
-- =====================================================
CREATE TABLE borrow_records (
    borrow_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    book_id INT NOT NULL,
    librarian_id INT NOT NULL,
    borrow_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE,
    status ENUM('borrowed', 'returned', 'lost') DEFAULT 'borrowed',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
    FOREIGN KEY (librarian_id) REFERENCES librarians(librarian_id),
    INDEX idx_student (student_id),
    INDEX idx_book (book_id),
    INDEX idx_status (status),
    INDEX idx_due_date (due_date),
    INDEX idx_return_date (return_date)
);

-- =====================================================
-- 12. FINES TABLE (Normalized - clean structure)
-- =====================================================
CREATE TABLE fines (
    fine_id INT PRIMARY KEY AUTO_INCREMENT,
    borrow_id INT NOT NULL,
    student_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    reason VARCHAR(255),
    status ENUM('pending', 'paid', 'waived') DEFAULT 'pending',
    issued_date DATE NOT NULL,
    paid_date DATE,
    issued_by INT,
    FOREIGN KEY (borrow_id) REFERENCES borrow_records(borrow_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (issued_by) REFERENCES librarians(librarian_id),
    INDEX idx_student (student_id),
    INDEX idx_status (status),
    INDEX idx_issued_date (issued_date)
);

-- =====================================================
-- 13. AUDIT LOGS TABLE
-- =====================================================
CREATE TABLE audit_logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    actor_type ENUM('admin', 'librarian', 'student'),
    actor_id INT,
    action VARCHAR(100),
    table_name VARCHAR(50),
    record_id INT,
    old_data JSON,
    new_data JSON,
    ip_address VARCHAR(45),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_actor (actor_type, actor_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_action (action)
);

-- =====================================================
-- VIEWS
-- =====================================================

-- View for book availability (computed dynamically)
CREATE OR REPLACE VIEW book_availability AS
SELECT 
    b.book_id,
    b.title,
    GROUP_CONCAT(DISTINCT a.name ORDER BY ba.author_order SEPARATOR ', ') as authors,
    GROUP_CONCAT(DISTINCT c.name SEPARATOR ', ') as categories,
    b.isbn,
    b.publisher,
    b.publication_year,
    b.total_copies,
    COALESCE(b.total_copies - COUNT(DISTINCT br.borrow_id), b.total_copies) as available_copies,
    COALESCE(COUNT(DISTINCT br.borrow_id), 0) as borrowed_copies,
    CASE 
        WHEN (b.total_copies - COALESCE(COUNT(DISTINCT br.borrow_id), 0)) > 0 
        THEN 'Available' 
        ELSE 'Not Available' 
    END as availability_status,
    b.location
FROM books b
LEFT JOIN book_authors ba ON b.book_id = ba.book_id
LEFT JOIN authors a ON ba.author_id = a.author_id
LEFT JOIN books_categories bc ON b.book_id = bc.book_id
LEFT JOIN categories c ON bc.category_id = c.category_id
LEFT JOIN borrow_records br ON b.book_id = br.book_id AND br.status = 'borrowed'
GROUP BY b.book_id;

-- View for current borrowings
CREATE OR REPLACE VIEW current_borrowings AS
SELECT 
    br.borrow_id,
    s.student_number,
    s.full_name as student_name,
    s.email as student_email,
    s.department,
    b.book_id,
    b.title,
    b.isbn,
    GROUP_CONCAT(DISTINCT a.name ORDER BY ba.author_order SEPARATOR ', ') as authors,
    br.borrow_date,
    br.due_date,
    DATEDIFF(CURDATE(), br.due_date) as days_overdue,
    CASE 
        WHEN br.due_date < CURDATE() AND br.status = 'borrowed' 
        THEN DATEDIFF(CURDATE(), br.due_date) * 10
        ELSE 0
    END as calculated_fine,
    l.employee_id as librarian_employee_id
FROM borrow_records br
JOIN students s ON br.student_id = s.student_id
JOIN books b ON br.book_id = b.book_id
LEFT JOIN book_authors ba ON b.book_id = ba.book_id
LEFT JOIN authors a ON ba.author_id = a.author_id
JOIN librarians l ON br.librarian_id = l.librarian_id
WHERE br.status = 'borrowed'
GROUP BY br.borrow_id;

-- View for overdue books
CREATE OR REPLACE VIEW overdue_books AS
SELECT 
    br.borrow_id,
    s.student_number,
    s.full_name as student_name,
    s.email as student_email,
    s.phone as student_phone,
    b.title,
    b.isbn,
    GROUP_CONCAT(DISTINCT a.name ORDER BY ba.author_order SEPARATOR ', ') as authors,
    br.borrow_date,
    br.due_date,
    DATEDIFF(CURDATE(), br.due_date) as days_overdue,
    DATEDIFF(CURDATE(), br.due_date) * 10 as calculated_fine
FROM borrow_records br
JOIN students s ON br.student_id = s.student_id
JOIN books b ON br.book_id = b.book_id
LEFT JOIN book_authors ba ON b.book_id = ba.book_id
LEFT JOIN authors a ON ba.author_id = a.author_id
WHERE br.status = 'borrowed' AND br.due_date < CURDATE();

-- View for student fines summary
CREATE OR REPLACE VIEW student_fines_summary AS
SELECT 
    s.student_id,
    s.student_number,
    s.full_name,
    s.email,
    COALESCE(SUM(CASE WHEN f.status = 'pending' THEN f.amount ELSE 0 END), 0) as total_pending_fines,
    COALESCE(SUM(CASE WHEN f.status = 'paid' THEN f.amount ELSE 0 END), 0) as total_paid_fines,
    COALESCE(COUNT(DISTINCT CASE WHEN f.status = 'pending' THEN f.fine_id END), 0) as pending_fine_count
FROM students s
LEFT JOIN fines f ON s.student_id = f.student_id
GROUP BY s.student_id;

-- =====================================================
-- TRIGGERS
-- =====================================================

DELIMITER $$

-- Trigger to update available copies when book is borrowed
CREATE TRIGGER update_available_copies_on_borrow
AFTER INSERT ON borrow_records
FOR EACH ROW
BEGIN
    -- Validate total_copies doesn't go negative (sanity check)
    IF (SELECT COUNT(*) FROM borrow_records WHERE book_id = NEW.book_id AND status = 'borrowed') 
       > (SELECT total_copies FROM books WHERE book_id = NEW.book_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Not enough copies available';
    END IF;
END$$

-- Trigger to ensure return_date is only set when status is returned
CREATE TRIGGER validate_return_date
BEFORE UPDATE ON borrow_records
FOR EACH ROW
BEGIN
    IF NEW.status = 'returned' AND NEW.return_date IS NULL THEN
        SET NEW.return_date = CURDATE();
    END IF;
    
    IF NEW.status != 'returned' AND NEW.return_date IS NOT NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Return date can only be set when status is returned';
    END IF;
END$$

-- Trigger to log admin creation
CREATE TRIGGER log_admin_creation
AFTER INSERT ON admins
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (actor_type, actor_id, action, table_name, record_id, new_data)
    VALUES ('admin', NEW.admin_id, 'CREATE', 'admins', NEW.admin_id, 
            JSON_OBJECT('email', NEW.email, 'full_name', NEW.full_name));
END$$

-- Trigger to log librarian creation
CREATE TRIGGER log_librarian_creation
AFTER INSERT ON librarians
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (actor_type, actor_id, action, table_name, record_id, new_data)
    VALUES ('librarian', NEW.librarian_id, 'CREATE', 'librarians', NEW.librarian_id, 
            JSON_OBJECT('email', NEW.email, 'employee_id', NEW.employee_id, 'full_name', NEW.full_name));
END$$

-- Trigger to log student creation
CREATE TRIGGER log_student_creation
AFTER INSERT ON students
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (actor_type, actor_id, action, table_name, record_id, new_data)
    VALUES ('student', NEW.student_id, 'CREATE', 'students', NEW.student_id, 
            JSON_OBJECT('email', NEW.email, 'student_number', NEW.student_number, 'full_name', NEW.full_name));
END$$

DELIMITER ;

-- =====================================================
-- STORED PROCEDURES
-- =====================================================

DELIMITER $$

-- Procedure to borrow a book
CREATE PROCEDURE borrow_book(
    IN p_student_number VARCHAR(20),
    IN p_book_id INT,
    IN p_librarian_employee_id VARCHAR(20),
    OUT p_message VARCHAR(255),
    OUT p_borrow_id INT
)
BEGIN
    DECLARE v_student_id INT;
    DECLARE v_librarian_id INT;
    DECLARE v_available_copies INT;
    DECLARE v_borrow_count INT;
    DECLARE v_user_status VARCHAR(20);
    DECLARE v_total_copies INT;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_message = 'Database error occurred';
    END;
    
    -- Get student ID and check status
    SELECT student_id, status INTO v_student_id, v_user_status
    FROM students
    WHERE student_number = p_student_number;
    
    IF v_student_id IS NULL THEN
        SET p_message = 'Student not found';
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Student not found';
    END IF;
    
    IF v_user_status != 'active' THEN
        SET p_message = 'Student account is not active';
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Student account is not active';
    END IF;
    
    -- Get librarian ID
    SELECT librarian_id INTO v_librarian_id
    FROM librarians 
    WHERE employee_id = p_librarian_employee_id;
    
    IF v_librarian_id IS NULL THEN
        SET p_message = 'Librarian not found';
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Librarian not found';
    END IF;
    
    -- Check if student can borrow more books (max 5)
    SELECT COUNT(*) INTO v_borrow_count 
    FROM borrow_records 
    WHERE student_id = v_student_id AND status = 'borrowed';
    
    IF v_borrow_count >= 5 THEN
        SET p_message = 'Student has reached maximum borrow limit (5 books)';
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Maximum borrow limit reached';
    END IF;
    
    -- Check total copies and available
    SELECT total_copies INTO v_total_copies
    FROM books WHERE book_id = p_book_id;
    
    IF v_total_copies IS NULL THEN
        SET p_message = 'Book not found';
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Book not found';
    END IF;
    
    SELECT COUNT(*) INTO v_available_copies
    FROM borrow_records 
    WHERE book_id = p_book_id AND status = 'borrowed';
    
    SET v_available_copies = v_total_copies - v_available_copies;
    
    IF v_available_copies <= 0 THEN
        SET p_message = 'No available copies of this book';
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No available copies';
    END IF;
    
    -- Start transaction
    START TRANSACTION;
    
    -- Create borrow record
    INSERT INTO borrow_records (student_id, book_id, librarian_id, borrow_date, due_date, status)
    VALUES (v_student_id, p_book_id, v_librarian_id, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY), 'borrowed');
    
    SET p_borrow_id = LAST_INSERT_ID();
    
    -- Log the action
    INSERT INTO audit_logs (actor_type, actor_id, action, table_name, record_id, new_data)
    VALUES ('librarian', v_librarian_id, 'BORROW', 'borrow_records', p_borrow_id, 
            JSON_OBJECT('student_number', p_student_number, 'book_id', p_book_id));
    
    SET p_message = 'Book borrowed successfully';
    COMMIT;
END$$

-- Procedure to return a book
CREATE PROCEDURE return_book(
    IN p_borrow_id INT,
    IN p_librarian_employee_id VARCHAR(20),
    OUT p_message VARCHAR(255),
    OUT p_fine_amount DECIMAL(10,2)
)
BEGIN
    DECLARE v_librarian_id INT;
    DECLARE v_student_id INT;
    DECLARE v_due_date DATE;
    DECLARE v_fine DECIMAL(10,2);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_message = 'Database error occurred';
    END;
    
    -- Get librarian ID
    SELECT librarian_id INTO v_librarian_id
    FROM librarians 
    WHERE employee_id = p_librarian_employee_id;
    
    IF v_librarian_id IS NULL THEN
        SET p_message = 'Librarian not found';
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Librarian not found';
    END IF;
    
    -- Get borrow record details
    SELECT student_id, due_date INTO v_student_id, v_due_date
    FROM borrow_records 
    WHERE borrow_id = p_borrow_id AND status = 'borrowed';
    
    IF v_student_id IS NULL THEN
        SET p_message = 'Borrow record not found or book already returned';
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid borrow record';
    END IF;
    
    -- Calculate fine if overdue (10 per day)
    IF CURDATE() > v_due_date THEN
        SET v_fine = DATEDIFF(CURDATE(), v_due_date) * 10;
        SET p_fine_amount = v_fine;
    ELSE
        SET v_fine = 0;
        SET p_fine_amount = 0;
    END IF;
    
    -- Start transaction
    START TRANSACTION;
    
    -- Update borrow record
    UPDATE borrow_records 
    SET return_date = CURDATE(), 
        status = 'returned'
    WHERE borrow_id = p_borrow_id;
    
    -- Create fine record if applicable
    IF v_fine > 0 THEN
        INSERT INTO fines (borrow_id, student_id, amount, reason, status, issued_date, issued_by)
        VALUES (p_borrow_id, v_student_id, v_fine, 'Overdue book', 'pending', CURDATE(), v_librarian_id);
    END IF;
    
    -- Log the action
    INSERT INTO audit_logs (actor_type, actor_id, action, table_name, record_id, new_data)
    VALUES ('librarian', v_librarian_id, 'RETURN', 'borrow_records', p_borrow_id, 
            JSON_OBJECT('return_date', CURDATE(), 'fine', v_fine));
    
    SET p_message = 'Book returned successfully';
    COMMIT;
END$$

-- Procedure to add new book
CREATE PROCEDURE add_book(
    IN p_title VARCHAR(255),
    IN p_author_names JSON,
    IN p_category_names JSON,
    IN p_isbn VARCHAR(13),
    IN p_publisher VARCHAR(100),
    IN p_publication_year YEAR,
    IN p_description TEXT,
    IN p_total_copies INT,
    IN p_location VARCHAR(50),
    IN p_librarian_employee_id VARCHAR(20),
    OUT p_message VARCHAR(255),
    OUT p_book_id INT
)
BEGIN
    DECLARE v_librarian_id INT;
    DECLARE i INT DEFAULT 0;
    DECLARE author_count INT;
    DECLARE author_name VARCHAR(100);
    DECLARE author_id INT;
    DECLARE category_count INT;
    DECLARE category_name VARCHAR(50);
    DECLARE category_id INT;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_message = 'Database error occurred';
    END;
    
    -- Get librarian ID
    SELECT librarian_id INTO v_librarian_id
    FROM librarians 
    WHERE employee_id = p_librarian_employee_id;
    
    IF v_librarian_id IS NULL THEN
        SET p_message = 'Librarian not found';
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Librarian not found';
    END IF;
    
    START TRANSACTION;
    
    -- Insert book
    INSERT INTO books (title, isbn, publisher, publication_year, description, total_copies, location, added_by)
    VALUES (p_title, p_isbn, p_publisher, p_publication_year, p_description, p_total_copies, p_location, v_librarian_id);
    
    SET p_book_id = LAST_INSERT_ID();
    
    -- Add authors (assumes JSON array format)
    SET author_count = JSON_LENGTH(p_author_names);
    SET i = 0;
    WHILE i < author_count DO
        SET author_name = JSON_UNQUOTE(JSON_EXTRACT(p_author_names, CONCAT('$[', i, ']')));
        
        -- Insert or get author
        INSERT IGNORE INTO authors (name) VALUES (author_name);
        SELECT author_id INTO author_id FROM authors WHERE name = author_name;
        
        -- Link author to book
        INSERT INTO book_authors (book_id, author_id, author_order)
        VALUES (p_book_id, author_id, i + 1);
        
        SET i = i + 1;
    END WHILE;
    
    -- Add categories (assumes JSON array format)
    SET category_count = JSON_LENGTH(p_category_names);
    SET i = 0;
    WHILE i < category_count DO
        SET category_name = JSON_UNQUOTE(JSON_EXTRACT(p_category_names, CONCAT('$[', i, ']')));
        
        -- Insert or get category
        INSERT IGNORE INTO categories (name) VALUES (category_name);
        SELECT category_id INTO category_id FROM categories WHERE name = category_name;
        
        -- Link category to book
        INSERT INTO books_categories (book_id, category_id)
        VALUES (p_book_id, category_id);
        
        SET i = i + 1;
    END WHILE;
    
    -- Log the action
    INSERT INTO audit_logs (actor_type, actor_id, action, table_name, record_id, new_data)
    VALUES ('librarian', v_librarian_id, 'CREATE', 'books', p_book_id, 
            JSON_OBJECT('title', p_title, 'isbn', p_isbn, 'total_copies', p_total_copies));
    
    SET p_message = 'Book added successfully';
    COMMIT;
END$$

-- Procedure to pay fine
CREATE PROCEDURE pay_fine(
    IN p_fine_id INT,
    IN p_librarian_employee_id VARCHAR(20),
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_librarian_id INT;
    DECLARE v_amount DECIMAL(10,2);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_message = 'Database error occurred';
    END;
    
    -- Get librarian ID
    SELECT librarian_id INTO v_librarian_id
    FROM librarians 
    WHERE employee_id = p_librarian_employee_id;
    
    IF v_librarian_id IS NULL THEN
        SET p_message = 'Librarian not found';
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Librarian not found';
    END IF;
    
    -- Get fine details
    SELECT amount INTO v_amount
    FROM fines 
    WHERE fine_id = p_fine_id AND status = 'pending';
    
    IF v_amount IS NULL THEN
        SET p_message = 'Fine not found or already paid';
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid fine';
    END IF;
    
    START TRANSACTION;
    
    -- Update fine status
    UPDATE fines 
    SET status = 'paid', 
        paid_date = CURDATE() 
    WHERE fine_id = p_fine_id;
    
    -- Log the action
    INSERT INTO audit_logs (actor_type, actor_id, action, table_name, record_id, new_data)
    VALUES ('librarian', v_librarian_id, 'PAY_FINE', 'fines', p_fine_id, 
            JSON_OBJECT('amount', v_amount, 'paid_date', CURDATE()));
    
    SET p_message = 'Fine paid successfully';
    COMMIT;
END$$

DELIMITER ;

-- =====================================================
-- SAMPLE DATA
-- =====================================================

-- Insert admins
INSERT INTO admins (email, password_hash, full_name, phone, admin_level, status) VALUES 
('admin@library.com', '$2y$10$YourHashedPasswordHere', 'John Admin', '+1234567890', 'super', 'active');

-- Insert librarians
INSERT INTO librarians (email, password_hash, full_name, employee_id, position, hire_date, phone, shift_schedule, department, status) VALUES 
('librarian1@library.com', '$2y$10$YourHashedPasswordHere', 'Jane Librarian', 'LIB001', 'Senior Librarian', '2023-01-15', '+1234567891', '9:00 AM - 5:00 PM', 'Circulation', 'active'),
('librarian2@library.com', '$2y$10$YourHashedPasswordHere', 'Mark Librarian', 'LIB002', 'Junior Librarian', '2024-01-10', '+1234567892', '1:00 PM - 9:00 PM', 'Reference', 'active');

-- Insert students
INSERT INTO students (email, password_hash, full_name, phone, student_number, department, year_level, section, status) VALUES
('student1@library.com', '$2y$10$YourHashedPasswordHere', 'Bob Student', '+1234567893', '241-0001', 'Computer Science', 3, 'A', 'active'),
('student2@library.com', '$2y$10$YourHashedPasswordHere', 'Alice Student', '+1234567894', '241-0002', 'Information Technology', 2, 'B', 'active'),
('student3@library.com', '$2y$10$YourHashedPasswordHere', 'Charlie Student', '+1234567895', '241-0003', 'Computer Science', 1, 'A', 'active');

-- Insert authors
INSERT INTO authors (name) VALUES 
('Robert C. Martin'),
('Erich Gamma'),
('Steve McConnell'),
('Eric Freeman'),
('Brian W. Kernighan'),
('Thomas H. Cormen');

-- Insert categories
INSERT INTO categories (name) VALUES 
('Programming'),
('Software Design'),
('Computer Science'),
('Algorithms');

-- Insert books
INSERT INTO books (isbn, title, publisher, publication_year, description, total_copies, location, added_by) VALUES 
('9780132350884', 'Clean Code: A Handbook of Agile Software Craftsmanship', 'Prentice Hall', 2008, 'A comprehensive guide to writing clean, maintainable code', 3, 'A-101', 1),
('9780201633610', 'Design Patterns: Elements of Reusable Object-Oriented Software', 'Addison-Wesley', 1994, 'Classic book on software design patterns', 2, 'A-102', 1),
('9780735619678', 'Code Complete: A Practical Handbook of Software Construction', 'Microsoft Press', 2004, 'Practical guide to software construction', 2, 'A-101', 2),
('9780596007126', 'Head First Design Patterns', "O'Reilly Media", 2004, 'Brain-friendly guide to design patterns', 3, 'A-103', 2),
('9780131103627', 'The C Programming Language', 'Prentice Hall', 1988, 'Classic book on C programming', 1, 'B-101', 1),
('9780262033848', 'Introduction to Algorithms', 'MIT Press', 2009, 'Comprehensive introduction to algorithms', 2, 'B-102', 1);

-- Link books to authors
INSERT INTO book_authors (book_id, author_id, author_order) VALUES 
(1, 1, 1),
(2, 2, 1),
(3, 3, 1),
(4, 4, 1),
(5, 5, 1),
(6, 6, 1);

-- Link books to categories
INSERT INTO books_categories (book_id, category_id) VALUES 
(1, 1),
(2, 2),
(3, 1),
(4, 2),
(5, 1),
(6, 4);

-- Insert sample borrow records
INSERT INTO borrow_records (student_id, book_id, librarian_id, borrow_date, due_date, status) VALUES 
(1, 1, 1, DATE_SUB(CURDATE(), INTERVAL 5 DAY), DATE_ADD(CURDATE(), INTERVAL 9 DAY), 'borrowed'),
(2, 3, 1, DATE_SUB(CURDATE(), INTERVAL 10 DAY), DATE_SUB(CURDATE(), INTERVAL 4 DAY), 'borrowed'),
(3, 5, 2, DATE_SUB(CURDATE(), INTERVAL 2 DAY), DATE_ADD(CURDATE(), INTERVAL 12 DAY), 'borrowed');
