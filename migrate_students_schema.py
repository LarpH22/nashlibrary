import pymysql
from backend.config import Config

conn = pymysql.connect(
    host=Config.DB_HOST,
    port=int(Config.DB_PORT),
    user=Config.DB_USER,
    password=Config.DB_PASSWORD,
    database=Config.DB_NAME
)

cursor = conn.cursor()

try:
    # Disable foreign key checks temporarily
    cursor.execute("SET FOREIGN_KEY_CHECKS=0")
    print("Disabled foreign key checks")
    
    # Drop dependent tables (they're empty)
    cursor.execute("DROP TABLE IF EXISTS fines")
    cursor.execute("DROP TABLE IF EXISTS borrow_records")
    print("Dropped dependent tables (borrow_records, fines)")
    
    # Drop the old students table
    cursor.execute("DROP TABLE IF EXISTS students")
    print("Dropped old students table")
    
    # Re-enable foreign key checks
    cursor.execute("SET FOREIGN_KEY_CHECKS=1")
    print("Re-enabled foreign key checks")
    
    # Create new students table with correct schema
    cursor.execute("""
    CREATE TABLE students (
        student_id INT PRIMARY KEY AUTO_INCREMENT,
        email VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        full_name VARCHAR(100) NOT NULL,
        student_number VARCHAR(20) UNIQUE NOT NULL,
        department VARCHAR(100),
        year_level INT,
        section VARCHAR(10),
        borrowed_books_count INT DEFAULT 0,
        total_fines DECIMAL(10,2) DEFAULT 0.00,
        library_card_number VARCHAR(20) UNIQUE,
        expiration_date DATE,
        registration_document VARCHAR(255),
        is_verified BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_email (email),
        INDEX idx_student_number (student_number),
        INDEX idx_library_card (library_card_number)
    )
    """)
    print("Created new students table with correct schema")
    
    # Create borrow_records table (no librarian_id references, simplified)
    cursor.execute("""
    CREATE TABLE borrow_records (
        borrow_id INT PRIMARY KEY AUTO_INCREMENT,
        student_id INT NOT NULL,
        book_id INT NOT NULL,
        borrow_date DATE NOT NULL,
        due_date DATE NOT NULL,
        return_date DATE,
        status ENUM('borrowed', 'returned', 'overdue', 'lost') DEFAULT 'borrowed',
        notes TEXT,
        fine_amount DECIMAL(10,2) DEFAULT 0.00,
        fine_paid BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
        FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
        INDEX idx_student (student_id),
        INDEX idx_status (status),
        INDEX idx_due_date (due_date)
    )
    """)
    print("Created borrow_records table")
    
    # Create fines table
    cursor.execute("""
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
        FOREIGN KEY (borrow_id) REFERENCES borrow_records(borrow_id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
        INDEX idx_status (status)
    )
    """)
    print("Created fines table")
    
    conn.commit()
    print("Database updated successfully!")
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()
