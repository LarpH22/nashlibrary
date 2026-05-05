# LIBRASYS Rubric Review

Source reviewed: `IT2206-IT2211-Rubrics-2026.xlsx`

## Rubric Assessment

The rubric is effective as a high-level evaluation guide because it covers the major grading areas for a library management system:

- System development: functionality, performance, usability, security, maintainability, and reliability.
- Database management: integrity, design, query performance, security, scalability, and maintainability.

The main weakness is that the rubric does not define measurable scoring levels. For example, "Security" is worth 15 points, but the sheet does not distinguish between basic login, role-based access, validated uploads, secure password storage, and production-safe configuration. Evaluators may score inconsistently unless the team prepares evidence for each category.

## Evidence To Prepare

- Functional suitability: show role dashboards for admin, librarian, and student; book search; borrowing; returns; fines; reservations; e-books; registration approvals.
- Performance efficiency: demonstrate paginated book, category, author, reservation, and search views.
- Usability: show cleaned login/register pages, landing hero, accessible buttons, and in-app status messages.
- Security: show JWT authentication, role routes, password hashing, validation, upload restrictions, security headers, restricted CORS, and non-debug server mode.
- Maintainability: explain layered backend structure and React feature folders.
- Reliability: show consistent JSON errors, pagination clamping, return/reservation state handling, and document-load error handling.
- Database integrity/design: present the 3NF schema, junction tables, foreign keys, constraints, and reservations table.
- Query performance/scalability: present indexes for search, loans, copies, reservations, students, and fines.

## System Improvements Made From Review

- Removed hard-coded Flask debug mode and made it controlled by `FLASK_DEBUG`.
- Reduced sensitive startup logging and browser console logging.
- Restricted CORS origins instead of allowing all origins.
- Replaced registration-document `alert()` calls with in-app status messaging.
- Updated the landing page CTA behavior.
- Updated the canonical SQL schema to include reservations and the `reserved` copy status.
- Added composite indexes for common active-loan and student-loan queries.
