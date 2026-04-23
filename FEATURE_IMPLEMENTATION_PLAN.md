# Student Dashboard - Missing Features Implementation Plan

## Priority Ranking: 1 (High Impact) → 3 (Lower Priority)

---

## 1. BOOK MANAGEMENT FEATURES

### 1.1 Book Renewal (Priority: 1 - High)
**Goal:** Allow students to extend due dates by 14 days (max 3 times per book)

**Database Changes:**
```sql
ALTER TABLE borrow_records ADD COLUMN renewal_count INT DEFAULT 0;
ALTER TABLE borrow_records ADD COLUMN last_renewal_date DATE;
```

**Backend API - NEW ROUTE:**
```
POST /borrowings/<borrow_id>/renew
- Validate: book not overdue, renewal_count < 3
- Update: due_date = current_due_date + 14 days, renewal_count++
- Return: new due date
```

**Frontend Changes:**
- Add "Renew" button in "Currently Borrowed" section (My Books tab)
- Show renewal count badge: "Renewals: 2/3"
- Disable button if max renewals reached or book is overdue

---

### 1.2 Hold/Reserve System (Priority: 1 - High)
**Goal:** Allow students to reserve unavailable books; auto-notify when available

**Database Changes:**
```sql
CREATE TABLE reserves (
    reserve_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    book_id INT NOT NULL,
    reserve_date DATE NOT NULL,
    expiry_date DATE,
    status ENUM('active', 'notified', 'collected', 'expired') DEFAULT 'active',
    position INT DEFAULT 0,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (book_id) REFERENCES books(book_id),
    INDEX idx_status (status)
);
```

**Backend API - NEW ROUTES:**
```
POST /reserves - Create hold
GET /reserves - List user's holds with queue position
DELETE /reserves/<reserve_id> - Cancel hold
```

**Frontend Changes:**
- In Catalog tab: Change "Not Available" button to "Reserve Book"
- New "My Reserves" section showing queue position
- Show "You're #3 in queue" message

---

### 1.3 Detailed Book Modal (Priority: 1 - High)
**Goal:** Show comprehensive book info on click

**Backend API - EXISTING ROUTE TO ENHANCE:**
```
GET /books/<book_id> (if exists, else create)
- Return: title, author, isbn, category, description, 
          published_date, total_copies, available_copies, 
          average_rating, number_of_reviews, cover_url
```

**Frontend Changes:**
- Create `BookDetailModal.jsx` component
- Triggered from: Catalog cards, Search results, Dashboard new arrivals
- Display: Cover, details, reviews section, rating stars
- Actions: Borrow, Reserve, or Save for Later buttons

---

### 1.4 Ratings & Reviews (Priority: 2 - Medium)
**Goal:** Students rate and review books they've read

**Database Changes:**
```sql
CREATE TABLE reviews (
    review_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    book_id INT NOT NULL,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    review_text TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    helpful_count INT DEFAULT 0,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (book_id) REFERENCES books(book_id),
    UNIQUE KEY unique_student_book (student_id, book_id)
);
```

**Backend API - NEW ROUTES:**
```
POST /reviews - Create/update review
GET /books/<book_id>/reviews - List reviews for book
PUT /reviews/<review_id> - Update own review
DELETE /reviews/<review_id> - Delete own review
```

**Frontend Changes:**
- In History tab: "Write Review" button appears after return_date is set
- In BookDetailModal: Show average rating and reviews list
- Create ReviewForm component

---

## 2. ACCOUNT & FINE MANAGEMENT

### 2.1 Fine/Penalty Tracking (Priority: 1 - High)
**Goal:** Display outstanding fines and payment status

**Backend API - EXISTING BUT ENHANCE:**
```
GET /student/fines - Get current student's fines
- Include: fine_id, reason, amount, status, due_date, book_title
- Filter: status IN ('pending', 'partial')

POST /fines/<fine_id>/pay - Record payment
- Payment method, amount, receipt
```

**Frontend Changes:**
- New card in dashboard hero section: "Outstanding Fines: $X.XX"
- Color coding: Green (paid), Red (overdue), Yellow (due soon)
- Click to view detailed fines modal with book details
- Show: "1 book overdue - $2.50 fine/day" warning

---

### 2.2 Account Balance & Limits Display (Priority: 1 - High)
**Goal:** Show borrowing limits and current usage

**Database Enhancement:**
```sql
ALTER TABLE students ADD COLUMN borrowing_limit INT DEFAULT 10;
ALTER TABLE students ADD COLUMN max_renewal_count INT DEFAULT 3;
```

**Backend API - NEW ROUTE:**
```
GET /student/limits
- Return: borrowing_limit, borrowed_books_count, max_renewal_count,
          max_hold_count, hold_count, account_status
```

**Frontend Changes:**
- New card: "Borrowing Status"
  - Bar chart: "5 of 10 books borrowed"
  - "3 of 3 holds active"
  - Color indicator: Green (OK), Yellow (caution), Red (limit reached)

---

## 3. ANALYTICS & RECOMMENDATIONS

### 3.1 Reading Goals (Priority: 2 - Medium)
**Goal:** Students set monthly/yearly reading targets

**Database Changes:**
```sql
CREATE TABLE reading_goals (
    goal_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    goal_type ENUM('monthly', 'yearly') DEFAULT 'monthly',
    target_count INT NOT NULL,
    current_count INT DEFAULT 0,
    created_date DATE,
    deadline DATE,
    status ENUM('active', 'completed', 'abandoned') DEFAULT 'active',
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);
```

**Frontend Changes:**
- Dashboard section: "Reading Goal for April 2026"
- Progress bar: "6 of 12 books read"
- Button: "Set a Goal" or "Edit Goal"

---

### 3.2 Personalized Recommendations (Priority: 2 - Medium)
**Goal:** Show books based on borrowing history

**Backend API - NEW ROUTE:**
```
GET /student/recommendations
- Logic: Find top 3 categories from student's history
- Return: 6-8 books matching those categories + high ratings
- Exclude: Already borrowed, wishlist items
```

**Frontend Changes:**
- New section in Dashboard tab: "Recommended for You"
- Shows: Cover + title + author + rating
- Action: "Borrow" or "Save for Later"

---

## 4. SUPPORT & HELP

### 4.1 FAQ Section (Priority: 3 - Lower)
**Goal:** In-app FAQ for common questions

**Frontend Implementation:**
- Create `FAQPanel.jsx` component
- Accessible from: Sidebar link or help icon
- Categories: "Borrowing", "Fines", "Accounts", "Technical"
- Searchable with keywords

**No backend required** - Static content in component

---

### 4.2 Help Docs & Contact (Priority: 3 - Lower)
**Goal:** Library contact info and documentation links

**Frontend Implementation:**
- New modal: "Help & Support"
- Sections:
  - "Contact Library" - email, phone, hours
  - "Documentation" - links to guides
  - "Report Issue" - feedback form (optional backend)

**Backend API - NEW ROUTE (Optional):**
```
POST /feedback
- Store: email, subject, message, timestamp
- For admin review
```

---

## 5. NOTIFICATIONS PANEL

### 5.1 Notification Center (Priority: 1 - High)
**Goal:** Actual working notification display

**Database Changes:**
```sql
CREATE TABLE notifications (
    notification_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    type ENUM('book_due', 'book_returned', 'reservation_ready', 'fine_issued') DEFAULT 'book_due',
    title VARCHAR(255) NOT NULL,
    message TEXT,
    link VARCHAR(255),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    INDEX idx_is_read (is_read)
);
```

**Backend API - NEW ROUTES:**
```
GET /notifications - List unread notifications
POST /notifications/<notification_id>/read - Mark as read
DELETE /notifications/<notification_id> - Dismiss
```

**Frontend Changes:**
- Replace "Notifications" button with badge counter
- Click opens NotificationPanel showing:
  - Unread first
  - Grouped by type
  - Dismiss option on each
  - "Mark all as read" button

**Auto-Trigger Notifications When:**
- Book due in 3 days
- Book returned successfully
- Hold becomes available
- Fine issued

---

## 6. ENHANCED PROFILE

### 6.1 Extended Profile Fields (Priority: 2 - Medium)
**Goal:** More comprehensive user information

**Database Changes:**
```sql
ALTER TABLE students ADD COLUMN library_card_number VARCHAR(50) UNIQUE;
ALTER TABLE students ADD COLUMN preferred_genre VARCHAR(100);
ALTER TABLE students ADD COLUMN date_of_birth DATE;
ALTER TABLE students ADD COLUMN blood_type VARCHAR(5);
ALTER TABLE students ADD COLUMN emergency_contact VARCHAR(100);
ALTER TABLE students ADD COLUMN emergency_phone VARCHAR(20);
```

**Frontend Changes:**
- Expand Profile Modal with new fields
- Display library card number prominently
- Show card expiry date

---

### 6.2 Account History/Activity Log (Priority: 2 - Medium)
**Goal:** Timeline of account activities

**Backend API - NEW ROUTE:**
```
GET /student/activity-log
- Return: last 30 days of:
  - Books borrowed
  - Books returned
  - Fines issued/paid
  - Reserves made/collected
  - Profile updates
  - Sorted by date (newest first)
```

**Frontend Changes:**
- New tab in Profile Modal: "Activity History"
- Timeline view with icons:
  - 📚 Borrowed "Book Title"
  - ✅ Returned "Book Title"
  - 💰 Paid fine $5.00
  - 📮 Reserved "Book Title"

---

## IMPLEMENTATION ROADMAP

### Phase 1 (Week 1) - Critical Features
1. Fine/Penalty Tracking
2. Borrowing Limits Display
3. Notification Panel (backend + frontend)
4. Book Renewal

### Phase 2 (Week 2) - Enhanced Book Management
5. Detailed Book Modal
6. Hold/Reserve System
7. Ratings & Reviews

### Phase 3 (Week 3) - Analytics & Support
8. Reading Goals
9. Personalized Recommendations
10. Extended Profile Fields
11. Activity Log

### Phase 4 (Week 4) - Polish & Support
12. FAQ/Help Documentation
13. Contact/Support Form
14. Testing & Bug Fixes

---

## TESTING CHECKLIST

- [ ] Renewal: Verify 14-day extension, max 3 renewals
- [ ] Reserves: Queue position updates, auto-notification
- [ ] Fines: Accurate calculation, payment recording
- [ ] Notifications: Real-time delivery, proper dismissal
- [ ] Ratings: Unique per student+book, display average
- [ ] Goals: Progress tracking, deadline alerts
- [ ] Recommendations: Accurate filtering, no duplicates
- [ ] Profile: All fields update correctly, card display

---

## FILE STRUCTURE SUMMARY

**Backend Routes to Add:**
- `/borrowings/<id>/renew`
- `/reserves` (POST, GET, DELETE)
- `/reviews` (POST, GET, PUT, DELETE)
- `/student/fines`
- `/student/limits`
- `/student/recommendations`
- `/notifications` (GET, POST, DELETE)
- `/student/activity-log`
- `/feedback` (optional)

**Frontend Components to Create:**
- `BookDetailModal.jsx`
- `ReviewForm.jsx`
- `NotificationPanel.jsx`
- `FAQPanel.jsx`
- `HelpModal.jsx`
- `ReadingGoalModal.jsx`
- `ActivityLog.jsx`

**Database Tables to Create:**
- `reserves`
- `reviews`
- `reading_goals`
- `notifications`
- `feedback` (optional)

---

## QUICK START: Implement First Feature

**Choose: Fine/Penalty Tracking (5-6 hours)**

1. Backend:
   - Create `GET /student/fines` endpoint
   - Test with Postman

2. Frontend:
   - Create `FinesCard.jsx` component
   - Add to dashboard hero
   - Show total amount and status

3. Styling:
   - Red for overdue
   - Yellow for pending
   - Green for paid

**This gives highest user value with minimal complexity.**
