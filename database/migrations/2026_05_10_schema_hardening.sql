-- LIBRASYS schema hardening migration
-- Generated after live schema review on 2026-05-10.
-- Purpose: add missing relational constraints, remove redundant indexes, and
-- make derived book status consistent without deleting business data.
--
-- Run only after a verified backup. Test on a restored copy first.

START TRANSACTION;

-- 1) Data cleanup required before adding stricter constraints.
UPDATE reservations r
LEFT JOIN librarians l ON r.approved_by = l.librarian_id
SET r.approved_by = NULL
WHERE r.approved_by IS NOT NULL
  AND l.librarian_id IS NULL;

UPDATE books b
JOIN (
    SELECT
        book_id,
        COUNT(*) AS copy_count,
        SUM(status = 'available') AS available_count,
        SUM(status = 'borrowed') AS borrowed_count,
        SUM(status = 'maintenance') AS maintenance_count,
        SUM(status = 'lost') AS lost_count
    FROM book_copies
    GROUP BY book_id
) c ON c.book_id = b.book_id
SET
    b.total_copies = c.copy_count,
    b.status = CASE
        WHEN c.available_count > 0 THEN 'available'
        WHEN c.borrowed_count > 0 THEN 'borrowed'
        WHEN c.maintenance_count > 0 THEN 'maintenance'
        WHEN c.lost_count > 0 THEN 'lost'
        ELSE b.status
    END;

COMMIT;

-- 2) Missing foreign keys. These are written separately because MySQL/MariaDB
-- commits DDL implicitly.
ALTER TABLE borrow_records
    ADD CONSTRAINT fk_borrow_records_copy
    FOREIGN KEY (copy_id) REFERENCES book_copies(copy_id)
    ON DELETE SET NULL
    ON UPDATE CASCADE;

ALTER TABLE borrow_requests
    ADD CONSTRAINT fk_borrow_requests_student
    FOREIGN KEY (student_id) REFERENCES students(student_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
    ADD CONSTRAINT fk_borrow_requests_book
    FOREIGN KEY (book_id) REFERENCES books(book_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
    ADD CONSTRAINT fk_borrow_requests_copy
    FOREIGN KEY (copy_id) REFERENCES book_copies(copy_id)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
    ADD CONSTRAINT fk_borrow_requests_borrow
    FOREIGN KEY (borrow_id) REFERENCES borrow_records(borrow_id)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
    ADD CONSTRAINT fk_borrow_requests_approved_by
    FOREIGN KEY (approved_by) REFERENCES librarians(librarian_id)
    ON DELETE SET NULL
    ON UPDATE CASCADE;

ALTER TABLE reservations
    ADD CONSTRAINT fk_reservations_approved_by
    FOREIGN KEY (approved_by) REFERENCES librarians(librarian_id)
    ON DELETE SET NULL
    ON UPDATE CASCADE;

-- 3) Candidate key improvements. Live data currently has no NULL/duplicate
-- student numbers, so this is safe after validation.
ALTER TABLE students
    MODIFY student_number VARCHAR(20) NOT NULL,
    ADD UNIQUE KEY uq_students_student_number (student_number);

-- 4) Helpful indexes for current query patterns.
CREATE INDEX idx_books_title_isbn ON books (title, isbn);
CREATE INDEX idx_book_copies_book_status ON book_copies (book_id, status);
CREATE INDEX idx_borrow_records_copy_status_return ON borrow_records (copy_id, status, return_date);
CREATE INDEX idx_fines_payment_status ON fines (payment_status, status);
CREATE INDEX idx_fines_payment_reference ON fines (payment_reference);
CREATE INDEX idx_registration_requests_token ON registration_requests (verification_token);
CREATE INDEX idx_students_reset_token ON students (reset_token);
CREATE INDEX idx_students_verification_token ON students (verification_token);

-- 5) Redundant indexes. Keep unique keys; remove duplicate non-unique mirrors.
ALTER TABLE admins DROP INDEX idx_email;
ALTER TABLE librarians DROP INDEX idx_email;
ALTER TABLE students DROP INDEX idx_email;
ALTER TABLE registration_requests DROP INDEX idx_email;
ALTER TABLE authors DROP INDEX idx_name;
ALTER TABLE categories DROP INDEX idx_name;
ALTER TABLE books DROP INDEX idx_isbn;
ALTER TABLE book_copies DROP INDEX idx_barcode_value;
ALTER TABLE book_copies DROP INDEX idx_qr_token;

