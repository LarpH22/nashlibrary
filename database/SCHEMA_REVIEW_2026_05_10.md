# LIBRASYS Database Structure Review

Review date: 2026-05-10

## Scope

This review checked the live `library_system_v2` schema against repository migrations and current application queries. The live database has 18 tables:

`admins`, `librarians`, `students`, `registration_requests`, `authors`, `categories`, `books`, `book_authors`, `books_categories`, `book_copies`, `borrow_requests`, `borrow_records`, `reservations`, `loan_reminders`, `fines`, `ebooks`, `ebook_access_logs`, and `audit_logs`.

## Normalization Findings

The catalog and circulation core is mostly in 3NF:

- Books are separated from authors and categories through join tables.
- Physical inventory is separated into `book_copies`.
- Borrowing, reservations, fines, reminders, e-books, and access logs are separate entities.

Main normalization risks:

- `books.status` and `books.total_copies` are derived from `book_copies` and can drift.
- `students.borrowed_books_count` and `students.total_fines` are derived from `borrow_records` and `fines`.
- Authentication fields are duplicated across `admins`, `librarians`, and `students`.
- `ebooks.author` and `ebooks.category` duplicate catalog dimensions when `book_id` is present.
- Polymorphic actor fields such as `audit_logs.user_role/user_id` and `ebook_access_logs.actor_role/actor_id` cannot use direct foreign keys.

## Live Data Issues Found

- `books.total_copies` matches `book_copies` for all books.
- All `borrow_records.copy_id` values are present and match the related `book_id`.
- No duplicate active loans exist for the same copy.
- All student numbers are present and unique.
- 3 `books.status` values disagree with copy-level availability.
- 1 `reservations.approved_by` value references a missing librarian.

## Tables To Delete

No live production table should be dropped immediately.

Do not delete:

- `audit_logs`: needed for security/compliance.
- `registration_requests`: needed for approval and email verification workflow.
- `loan_reminders`: needed notification history.
- `ebook_access_logs`: needed e-book access audit.

Optional future consolidation:

- Replace separate auth storage in `admins`, `librarians`, `students` with a new `user_accounts` table, then keep role-profile tables. This is a phased refactor, not a safe one-step deletion.

## Columns To Remove Or Merge

Do not remove these until application code is updated:

- `books.status`: replace with computed availability from `book_copies`.
- `books.total_copies`: replace with `COUNT(book_copies.copy_id)`.
- `students.borrowed_books_count`: compute from active `borrow_records`.
- `students.total_fines`: compute from unpaid `fines`.
- `students.is_verified`: merge into `email_verified`.
- `students.proof_file`: merge into `registration_document`.
- `ebooks.author`, `ebooks.category`: use `books -> book_authors/books_categories` when `book_id` is not null.

## Relationships To Fix

Add missing foreign keys:

- `borrow_records.copy_id -> book_copies.copy_id`
- `borrow_requests.student_id -> students.student_id`
- `borrow_requests.book_id -> books.book_id`
- `borrow_requests.copy_id -> book_copies.copy_id`
- `borrow_requests.borrow_id -> borrow_records.borrow_id`
- `borrow_requests.approved_by -> librarians.librarian_id`
- `reservations.approved_by -> librarians.librarian_id`

Use `ON DELETE SET NULL` for historical actor/copy references that should not erase transaction history, and `ON DELETE CASCADE` only for dependent rows that have no meaning without the parent.

## Recommended Production Schema

Core identity:

- `user_accounts(user_account_id, email, password_hash, role, status, email_verified, last_login, created_at, updated_at)`
- `students(student_id, user_account_id, student_number, full_name, department, year_level, section, phone, address, registration_document, library_card_number, expiration_date)`
- `librarians(librarian_id, user_account_id, employee_id, full_name, position, department, phone, address)`
- `admins(admin_id, user_account_id, full_name, admin_level, permissions)`

Catalog:

- `books(book_id, isbn, title, publisher, published_date, description, cover_image_url, added_by, added_at, updated_at)`
- `authors(author_id, name, bio)`
- `categories(category_id, name, description)`
- `book_authors(book_id, author_id, author_order)`
- `book_categories(book_id, category_id)`
- `book_copies(copy_id, book_id, copy_code, barcode_value, qr_token, status, location, created_at, updated_at)`

Circulation:

- `borrow_records(borrow_id, student_id, book_id, copy_id, issued_by, borrow_date, due_date, return_date, status, created_at, updated_at)`
- `borrow_requests(request_id, student_id, book_id, copy_id, status, requested_at, decided_at, approved_by, due_date, borrow_id, rejection_reason)`
- `reservations(reservation_id, student_id, book_id, ready_copy_id, queue_position, status, reservation_date, expiration_date, approved_by, claimed_at, cancelled_at)`
- `fines(fine_id, borrow_id, student_id, amount, reason, status, payment_status, payment_method, payment_reference, receipt_path, issued_date, paid_date)`

Digital/library ops:

- `ebooks(ebook_id, book_id, title, original_filename, stored_filename, file_path, file_type, file_size, access_level, uploaded_by_role, uploaded_by_id, uploaded_at, qr_code_path)`
- `ebook_access_logs(access_id, ebook_id, actor_role, actor_id, action, accessed_at)`
- `notifications(notification_id, recipient_role, recipient_id, type, title, message, read_at, created_at)`
- `audit_logs(log_id, actor_role, actor_id, action, entity_type, entity_id, old_values, new_values, ip_address, user_agent, created_at)`
- `auth_tokens(token_id, account_role, account_id, token_hash, token_type, expires_at, used_at, created_at)`

## ERD Structure

```text
students 1--N borrow_records N--1 books
books 1--N book_copies
book_copies 1--N borrow_records
books N--M authors via book_authors
books N--M categories via books_categories
students 1--N reservations N--1 books
book_copies 1--N reservations as ready_copy_id
borrow_records 1--0..1 fines
borrow_records 1--N loan_reminders
books 1--N ebooks
ebooks 1--N ebook_access_logs
admins/librarians/students 1--N audit_logs as polymorphic actors
registration_requests -> students after approval
```

## Backup Plan

1. Stop writes or put the system in maintenance mode.
2. Create a full logical backup:
   `mysqldump --single-transaction --routines --triggers library_system_v2 > backups/library_system_v2_YYYYMMDD.sql`
3. Create a schema-only backup:
   `mysqldump --no-data library_system_v2 > backups/library_system_v2_schema_YYYYMMDD.sql`
4. Restore both to a staging database.
5. Run validation queries on staging.
6. Apply migration to staging.
7. Run application smoke tests: login, book search, scan issue, return, reservation, fine payment, e-book open/download.
8. Apply to production only after staging passes.

## Migration SQL

See `database/migrations/2026_05_10_schema_hardening.sql`.

This migration is intentionally conservative:

- It fixes current inconsistent rows.
- It adds missing FKs.
- It adds indexes for hot lookup paths.
- It removes duplicate non-unique indexes.
- It does not drop live tables or columns.

## Performance Recommendations

- Prefer copy-level availability from `book_copies(book_id, status)`.
- Use composite indexes for dashboard/list filters:
  - `borrow_records(student_id, status, due_date)`
  - `borrow_records(copy_id, status, return_date)`
  - `reservations(book_id, status, queue_position, reservation_date)`
  - `fines(payment_status, status)`
- Avoid maintaining count columns unless triggers or application transactions guarantee consistency.
- Consider FULLTEXT indexes for book title/description/author search when catalog grows.

## Validation Improvements

- Enforce `students.student_number NOT NULL UNIQUE`.
- Enforce active loan uniqueness per physical copy through application transaction locks; MySQL partial unique indexes are not available in the current style.
- Normalize token storage into hashed `auth_tokens` instead of storing raw reset/verification tokens on student rows.
- Use JSON columns for permissions/audit value snapshots if the MySQL/MariaDB version supports them.
- Use `DECIMAL(10,2)` for all monetary values and keep payment status transitions explicit.

## Final Production Direction

The safest production-ready direction is phased:

1. Apply schema hardening migration.
2. Update application code to stop writing derived columns.
3. Add views for `book_availability` and student balance summaries.
4. Introduce `user_accounts` and `auth_tokens`.
5. Backfill accounts from role tables.
6. Switch authentication to `user_accounts`.
7. Remove duplicated auth columns only after one release cycle.

