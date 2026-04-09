-- =====================================================
-- ONLINE LIBRARY MANAGEMENT SYSTEM - COMPLETE DATABASE
-- =====================================================

-- Drop existing tables if they exist (in correct order to avoid foreign key constraints)
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS fines;
DROP TABLE IF EXISTS borrow_records;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS librarians;
DROP TABLE IF EXISTS admins;
DROP TABLE IF EXISTS users;

-- =====================================================
-- 1. USERS TABLE (Base table for all roles)
-- =====================================================
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
);

-- =====================================================
-- 2. ADMINS TABLE (Admin-specific details)
-- =====================================================
CREATE TABLE admins (
    admin_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE NOT NULL,
    admin_level ENUM('super', 'senior', 'junior') DEFAULT 'junior',
    permissions TEXT, -- JSON format for admin permissions
    last_password_change TIMESTAMP,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- =====================================================
-- 3. LIBRARIANS TABLE (Librarian-specific details)
-- =====================================================
CREATE TABLE librarians (
    librarian_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE NOT NULL,
    employee_id VARCHAR(20) UNIQUE NOT NULL,
    position VARCHAR(50),
    hire_date DATE,
    shift_schedule VARCHAR(50),
    department VARCHAR(50),
    permissions TEXT, -- JSON format for specific permissions
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_employee_id (employee_id)
);

-- =====================================================
-- 4. STUDENTS TABLE (Student-specific details)
-- =====================================================
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
);

-- =====================================================
-- 5. BOOKS TABLE
-- =====================================================
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
    location VARCHAR(50), -- Shelf location
    added_by INT,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (added_by) REFERENCES users(user_id),
    INDEX idx_title (title),
    INDEX idx_author (author),
    INDEX idx_isbn (isbn),
    INDEX idx_category (category)
);

-- =====================================================
-- 6. BORROWING RECORDS TABLE
-- =====================================================
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
);

-- =====================================================
-- 7. FINES TABLE
-- =====================================================
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
);

-- =====================================================
-- 8. AUDIT LOGS TABLE
-- =====================================================
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
);

-- =====================================================
-- 9. TRIGGERS
-- =====================================================

-- Trigger to calculate fine when book is returned
DELIMITER $$
CREATE TRIGGER calculate_fine_on_return
BEFORE UPDATE ON borrow_records
FOR EACH ROW
BEGIN
    IF NEW.status = 'returned' AND OLD.status != 'returned' THEN
        IF NEW.return_date > OLD.due_date THEN
            SET NEW.fine_amount = DATEDIFF(NEW.return_date, OLD.due_date) * 10;
        END IF;
    END IF;
END$$

-- Trigger to update available copies when book is borrowed
CREATE TRIGGER update_available_copies_on_borrow
AFTER INSERT ON borrow_records
FOR EACH ROW
BEGIN
    UPDATE books 
    SET available_copies = available_copies - 1 
    WHERE book_id = NEW.book_id;
END$$

-- Trigger to update available copies when book is returned
CREATE TRIGGER update_available_copies_on_return
AFTER UPDATE ON borrow_records
FOR EACH ROW
BEGIN
    IF NEW.status = 'returned' AND OLD.status != 'returned' THEN
        UPDATE books 
        SET available_copies = available_copies + 1 
        WHERE book_id = NEW.book_id;
        
        UPDATE students 
        SET borrowed_books_count = borrowed_books_count - 1 
        WHERE student_id = NEW.student_id;
    END IF;
END$$

-- Trigger to log user creation
CREATE TRIGGER log_user_creation
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, action, table_name, record_id, new_data)
    VALUES (NEW.user_id, 'CREATE', 'users', NEW.user_id, 
            JSON_OBJECT('email', NEW.email, 'role', NEW.role, 'full_name', NEW.full_name));
END$$

DELIMITER ;

-- =====================================================
-- 10. VIEWS
-- =====================================================

-- View for student dashboard
CREATE OR REPLACE VIEW student_dashboard AS
SELECT 
    s.student_id,
    s.student_number,
    u.full_name,
    u.email,
    u.phone,
    s.department,
    s.year_level,
    s.borrowed_books_count,
    s.total_fines,
    s.library_card_number,
    COUNT(DISTINCT br.borrow_id) as current_borrowed,
    COALESCE(SUM(f.amount), 0) as pending_fines
FROM students s
JOIN users u ON s.user_id = u.user_id
LEFT JOIN borrow_records br ON s.student_id = br.student_id AND br.status = 'borrowed'
LEFT JOIN fines f ON s.student_id = f.student_id AND f.status = 'pending'
GROUP BY s.student_id;

-- View for current borrowings
CREATE OR REPLACE VIEW current_borrowings AS
SELECT 
    br.borrow_id,
    s.student_number,
    u.full_name as student_name,
    s.department,
    b.book_id,
    b.title,
    b.isbn,
    b.author,
    br.borrow_date,
    br.due_date,
    DATEDIFF(CURDATE(), br.due_date) as days_overdue,
    CASE 
        WHEN br.due_date < CURDATE() AND br.status = 'borrowed' 
        THEN DATEDIFF(CURDATE(), br.due_date) * 10
        ELSE 0
    END as calculated_fine,
    l.employee_id as librarian_employee_id,
    CONCAT(lib.full_name, ' (', l.employee_id, ')') as processed_by
FROM borrow_records br
JOIN students s ON br.student_id = s.student_id
JOIN users u ON s.user_id = u.user_id
JOIN books b ON br.book_id = b.book_id
JOIN librarians l ON br.librarian_id = l.librarian_id
JOIN users lib ON l.user_id = lib.user_id
WHERE br.status = 'borrowed';

-- View for overdue books
CREATE OR REPLACE VIEW overdue_books AS
SELECT 
    br.borrow_id,
    s.student_number,
    u.full_name as student_name,
    u.email as student_email,
    u.phone as student_phone,
    b.title,
    b.isbn,
    br.borrow_date,
    br.due_date,
    DATEDIFF(CURDATE(), br.due_date) as days_overdue,
    DATEDIFF(CURDATE(), br.due_date) * 10 as total_fine
FROM borrow_records br
JOIN students s ON br.student_id = s.student_id
JOIN users u ON s.user_id = u.user_id
JOIN books b ON br.book_id = b.book_id
WHERE br.status = 'borrowed' AND br.due_date < CURDATE();

-- View for book availability
CREATE OR REPLACE VIEW book_availability AS
SELECT 
    book_id,
    title,
    author,
    isbn,
    category,
    total_copies,
    available_copies,
    total_copies - available_copies as borrowed_copies,
    CASE 
        WHEN available_copies > 0 THEN 'Available'
        ELSE 'Not Available'
    END as availability_status,
    location
FROM books;

-- =====================================================
-- 11. STORED PROCEDURES
-- =====================================================

DELIMITER $$

-- Procedure to borrow a book
CREATE PROCEDURE borrow_book(
    IN p_student_number VARCHAR(20),
    IN p_book_id INT,
    IN p_librarian_employee_id VARCHAR(20),
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_student_id INT;
    DECLARE v_librarian_id INT;
    DECLARE v_available_copies INT;
    DECLARE v_borrow_count INT;
    DECLARE v_student_status VARCHAR(20);
    
    -- Get student ID and check status
    SELECT s.student_id, u.status INTO v_student_id, v_student_status
    FROM students s
    JOIN users u ON s.user_id = u.user_id
    WHERE s.student_number = p_student_number;
    
    IF v_student_id IS NULL THEN
        SET p_message = 'Student not found';
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Student not found';
    END IF;
    
    IF v_student_status != 'active' THEN
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
    SELECT borrowed_books_count INTO v_borrow_count 
    FROM students WHERE student_id = v_student_id;
    
    IF v_borrow_count >= 5 THEN
        SET p_message = 'Student has reached maximum borrow limit (5 books)';
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Student has reached maximum borrow limit';
    END IF;
    
    -- Check available copies
    SELECT available_copies INTO v_available_copies 
    FROM books WHERE book_id = p_book_id;
    
    IF v_available_copies <= 0 THEN
        SET p_message = 'No available copies of this book';
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No available copies';
    END IF;
    
    -- Start transaction
    START TRANSACTION;
    
    -- Create borrow record
    INSERT INTO borrow_records (student_id, book_id, librarian_id, borrow_date, due_date, status)
    VALUES (v_student_id, p_book_id, v_librarian_id, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY), 'borrowed');
    
    -- Update student borrow count
    UPDATE students 
    SET borrowed_books_count = borrowed_books_count + 1 
    WHERE student_id = v_student_id;
    
    -- Log the action
    INSERT INTO audit_logs (user_id, action, table_name, record_id, new_data)
    VALUES ((SELECT user_id FROM librarians WHERE librarian_id = v_librarian_id), 
            'BORROW', 'borrow_records', LAST_INSERT_ID(), 
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
    
    -- Calculate fine if overdue
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
        status = 'returned',
        fine_amount = v_fine
    WHERE borrow_id = p_borrow_id;
    
    -- Create fine record if applicable
    IF v_fine > 0 THEN
        INSERT INTO fines (borrow_id, student_id, amount, reason, status, issued_date, issued_by)
        VALUES (p_borrow_id, v_student_id, v_fine, 'Overdue book', 'pending', CURDATE(), 
                (SELECT user_id FROM librarians WHERE librarian_id = v_librarian_id));
        
        UPDATE students 
        SET total_fines = total_fines + v_fine 
        WHERE student_id = v_student_id;
    END IF;
    
    -- Log the action
    INSERT INTO audit_logs (user_id, action, table_name, record_id, new_data)
    VALUES ((SELECT user_id FROM librarians WHERE librarian_id = v_librarian_id), 
            'RETURN', 'borrow_records', p_borrow_id, 
            JSON_OBJECT('return_date', CURDATE(), 'fine', v_fine));
    
    SET p_message = 'Book returned successfully';
    COMMIT;
END$$

-- Procedure to add new book
CREATE PROCEDURE add_book(
    IN p_title VARCHAR(255),
    IN p_author VARCHAR(100),
    IN p_isbn VARCHAR(13),
    IN p_category VARCHAR(50),
    IN p_total_copies INT,
    IN p_librarian_employee_id VARCHAR(20),
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_librarian_user_id INT;
    
    -- Get librarian user ID
    SELECT user_id INTO v_librarian_user_id
    FROM librarians 
    WHERE employee_id = p_librarian_employee_id;
    
    IF v_librarian_user_id IS NULL THEN
        SET p_message = 'Librarian not found';
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Librarian not found';
    END IF;
    
    -- Insert book
    INSERT INTO books (title, author, isbn, category, total_copies, available_copies, added_by)
    VALUES (p_title, p_author, p_isbn, p_category, p_total_copies, p_total_copies, v_librarian_user_id);
    
    SET p_message = 'Book added successfully';
END$$

-- Procedure to pay fine
CREATE PROCEDURE pay_fine(
    IN p_fine_id INT,
    IN p_librarian_employee_id VARCHAR(20),
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_student_id INT;
    DECLARE v_amount DECIMAL(10,2);
    DECLARE v_librarian_user_id INT;
    
    -- Get librarian user ID
    SELECT user_id INTO v_librarian_user_id
    FROM librarians 
    WHERE employee_id = p_librarian_employee_id;
    
    IF v_librarian_user_id IS NULL THEN
        SET p_message = 'Librarian not found';
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Librarian not found';
    END IF;
    
    -- Get fine details
    SELECT student_id, amount INTO v_student_id, v_amount
    FROM fines 
    WHERE fine_id = p_fine_id AND status = 'pending';
    
    IF v_student_id IS NULL THEN
        SET p_message = 'Fine not found or already paid';
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid fine';
    END IF;
    
    -- Start transaction
    START TRANSACTION;
    
    -- Update fine status
    UPDATE fines 
    SET status = 'paid', 
        paid_date = CURDATE() 
    WHERE fine_id = p_fine_id;
    
    -- Update student total fines (optional - if you want to track total fines paid)
    -- UPDATE students SET total_fines = total_fines - v_amount WHERE student_id = v_student_id;
    
    -- Log the action
    INSERT INTO audit_logs (user_id, action, table_name, record_id, new_data)
    VALUES (v_librarian_user_id, 'PAY_FINE', 'fines', p_fine_id, 
            JSON_OBJECT('amount', v_amount, 'paid_date', CURDATE()));
    
    SET p_message = 'Fine paid successfully';
    COMMIT;
END$$

DELIMITER ;

-- =====================================================
-- 12. SAMPLE DATA
-- =====================================================

-- Insert users
INSERT INTO users (email, password_hash, full_name, phone, address, role, status) VALUES 
('admin@library.com', '$2y$10$YourHashedPasswordHere', 'John Admin', '+1234567890', '123 Admin St, City', 'admin', 'active'),
('librarian1@library.com', '$2y$10$YourHashedPasswordHere', 'Jane Librarian', '+1234567891', '456 Library Ave, City', 'librarian', 'active'),
('librarian2@library.com', '$2y$10$YourHashedPasswordHere', 'Mark Librarian', '+1234567892', '789 Library Ave, City', 'librarian', 'active'),
('student1@library.com', '$2y$10$YourHashedPasswordHere', 'Bob Student', '+1234567893', '321 University St, City', 'student', 'active'),
('student2@library.com', '$2y$10$YourHashedPasswordHere', 'Alice Student', '+1234567894', '654 University St, City', 'student', 'active'),
('student3@library.com', '$2y$10$YourHashedPasswordHere', 'Charlie Student', '+1234567895', '987 University St, City', 'student', 'active');

-- Insert admins
INSERT INTO admins (user_id, admin_level, permissions, two_factor_enabled) VALUES 
(1, 'super', '{"all": true, "manage_admins": true, "manage_librarians": true, "manage_students": true, "reports": true}', FALSE);

-- Insert librarians
INSERT INTO librarians (user_id, employee_id, position, hire_date, shift_schedule, department, permissions) VALUES 
(2, 'LIB001', 'Senior Librarian', '2023-01-15', '9:00 AM - 5:00 PM', 'Circulation', '{"borrow": true, "return": true, "add_books": true, "manage_fines": true}'),
(3, 'LIB002', 'Junior Librarian', '2024-01-10', '1:00 PM - 9:00 PM', 'Reference', '{"borrow": true, "return": true, "add_books": false, "manage_fines": false}');

-- Insert students
INSERT INTO students (user_id, student_number, department, year_level, section, library_card_number, expiration_date) VALUES 
(4, 'STU2024001', 'Computer Science', 3, 'A', 'CARD2024001', DATE_ADD(CURDATE(), INTERVAL 2 YEAR)),
(5, 'STU2024002', 'Information Technology', 2, 'B', 'CARD2024002', DATE_ADD(CURDATE(), INTERVAL 2 YEAR)),
(6, 'STU2024003', 'Computer Science', 1, 'A', 'CARD2024003', DATE_ADD(CURDATE(), INTERVAL 2 YEAR));

-- Insert books
INSERT INTO books (isbn, title, author, publisher, publication_year, category, description, total_copies, available_copies, location, added_by) VALUES 
('9780132350884', 'Clean Code: A Handbook of Agile Software Craftsmanship', 'Robert C. Martin', 'Prentice Hall', 2008, 'Programming', 'A comprehensive guide to writing clean, maintainable code', 3, 3, 'A-101', 1),
('9780201633610', 'Design Patterns: Elements of Reusable Object-Oriented Software', 'Erich Gamma', 'Addison-Wesley', 1994, 'Programming', 'Classic book on software design patterns', 2, 2, 'A-102', 1),
('9780735619678', 'Code Complete: A Practical Handbook of Software Construction', 'Steve McConnell', 'Microsoft Press', 2004, 'Programming', 'Practical guide to software construction', 2, 2, 'A-101', 2),
('9780596007126', 'Head First Design Patterns', 'Eric Freeman', "O'Reilly Media", 2004, 'Programming', 'Brain-friendly guide to design patterns', 3, 3, 'A-103', 2),
('9780131103627', 'The C Programming Language', 'Brian W. Kernighan', 'Prentice Hall', 1988, 'Programming', 'Classic book on C programming', 1, 1, 'B-101', 1),
('9780132350884', 'Introduction to Algorithms', 'Thomas H. Cormen', 'MIT Press', 2009, 'Computer Science', 'Comprehensive introduction to algorithms', 2, 2, 'B-102', 1);

-- Insert some sample borrow records (for testing)
INSERT INTO borrow_records (student_id, book_id, librarian_id, borrow_date, due_date, status) VALUES 
(1, 1, 1, DATE_SUB(CURDATE(), INTERVAL 5 DAY), DATE_ADD(CURDATE(), INTERVAL 9 DAY), 'borrowed'),
(2, 3, 1, DATE_SUB(CURDATE(), INTERVAL 10 DAY), DATE_SUB(CURDATE(), INTERVAL 4 DAY), 'borrowed'),
(3, 5, 2, DATE_SUB(CURDATE(), INTERVAL 2 DAY), DATE_ADD(CURDATE(), INTERVAL 12 DAY), 'borrowed');

-- Update student borrowed count
UPDATE students SET borrowed_books_count = 1 WHERE student_id = 1;
UPDATE students SET borrowed_books_count = 1 WHERE student_id = 2;
UPDATE students SET borrowed_books_count = 1 WHERE student_id = 3;
