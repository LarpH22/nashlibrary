import '../App.css'
import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'

function StudentDashboard({ user, onLogout }) {
  const [activePanel, setActivePanel] = useState('Search Books')
  const [books, setBooks] = useState([])
  const [borrowings, setBorrowings] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const menuItems = ['Search Books', 'My Borrowed Books', 'Profile', 'Support']

  useEffect(() => {
    fetchBooks()
    fetchBorrowings()
  }, [fetchBooks, fetchBorrowings])

  const fetchBooks = useCallback(async () => {
    try {
      const token = localStorage.getItem('token') || localStorage.getItem('access_token')
      const headers = token ? { Authorization: `Bearer ${token}` } : {}
      const query = searchQuery.trim() ? `?title=${encodeURIComponent(searchQuery.trim())}` : ''
      const response = await axios.get(`/student/books/search${query}`, { headers })
      setBooks(response.data.books || [])
    } catch (error) {
      console.error('Error fetching books:', error.response?.status, error.response?.data || error.message)
    }
  }, [searchQuery])

  const fetchBorrowings = useCallback(async () => {
    try {
      const response = await axios.get('/borrowings')
      setBorrowings(response.data)
    } catch (error) {
      console.error('Error fetching borrowings:', error)
    }
  }, [])

  const filteredBooks = books.filter((book) => {
    const q = searchQuery.toLowerCase()
    return (
      book.title?.toLowerCase().includes(q) ||
      book.author?.toLowerCase().includes(q) ||
      book.category?.toLowerCase().includes(q) ||
      book.book_id?.toString().includes(q)
    )
  })

  const studentBorrowings = borrowings.filter((item) => item.student_email === user?.email)

  const panelContent = {
    'Search Books': 'Search by title, author, or ISBN and add books to your reading list.',
    'My Borrowed Books': 'View due dates, return status, and renew any borrowed titles.',
    'Profile': `${user?.full_name || 'Student'} - Update your contact details and password.`,
    'Support': 'Contact support at support@librasys.edu for help.'
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Student Dashboard</h1>
        <div className="user-info">
          <span>Welcome, {user?.full_name || user?.username || 'Student'}</span>
          <button onClick={onLogout} className="logout-btn">Logout</button>
        </div>
      </header>
      <div className="dashboard-content">
        <div className="sidebar">
          <h3>Menu</h3>
          <ul>
            {menuItems.map((item) => (
              <li key={item} onClick={() => setActivePanel(item)} className={activePanel === item ? 'active-menu' : ''}>
                {item}
              </li>
            ))}
          </ul>
        </div>
        <main className="main-content">
          {activePanel === 'Search Books' && (
            <>
              <h2>Search Books</h2>
              <p>{panelContent['Search Books']}</p>
              <div className="search-panel">
                <input
                  type="text"
                  placeholder="Enter title, author, or ISBN"
                  className="text-input"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <button className="primary-btn" onClick={fetchBooks}>Refresh</button>
              </div>
              <div className="table-card">
                <h3>Search Results</h3>
                <ul>
                  {filteredBooks.length ? (
                    filteredBooks.map((book) => (
                      <li key={book.book_id}>
                        <strong>{book.title}</strong> by {book.author} <em>({book.category})</em>
                        <br />ISBN: {book.isbn} • Status: {book.status}
                      </li>
                    ))
                  ) : (
                    <li>No books found.</li>
                  )}
                </ul>
              </div>
            </>
          )}

          {activePanel === 'My Borrowed Books' && (
            <>
              <h2>My Borrowed Books</h2>
              <p>{panelContent['My Borrowed Books']}</p>
              <div className="table-card">
                <ul>
                  {studentBorrowings.length ? (
                    studentBorrowings.map((item) => (
                      <li key={item.borrow_id}>
                        <strong>{item.book_title || 'Unknown book'}</strong> - Due: {item.due_date} ({item.status})
                      </li>
                    ))
                  ) : (
                    <li>No borrowed book records found.</li>
                  )}
                </ul>
              </div>
            </>
          )}

          {activePanel === 'Profile' && (
            <>
              <h2>Profile</h2>
              <p>{panelContent['Profile']}</p>
              <div className="table-card">
                <p>Name: {user?.full_name || 'Student User'}</p>
                <p>Email: {user?.username || 'student1@library.com'}</p>
                <p>Student No: STU2024001</p>
              </div>
            </>
          )}

          {activePanel === 'Support' && (
            <>
              <h2>Support</h2>
              <p>{panelContent['Support']}</p>
              <div className="table-card">
                <p>Phone: +1 555 123 4567</p>
                <p>Email: support@librasys.edu</p>
                <p>FAQ: See the documentation for details.</p>
              </div>
            </>
          )}

          <div className="stats-grid">
            <div className="stat-card" onClick={() => setActivePanel('My Borrowed Books')}>
              <h4>Books Borrowed</h4>
              <p>3</p>
            </div>
            <div className="stat-card" onClick={() => setActivePanel('My Borrowed Books')}>
              <h4>Due Soon</h4>
              <p>1</p>
            </div>
            <div className="stat-card" onClick={() => setActivePanel('My Borrowed Books')}>
              <h4>Fines</h4>
              <p>$0.00</p>
            </div>
          </div>

          <div className="recent-activity">
            <h3>Recent Activity</h3>
            <ul>
              <li>Borrowed “The Great Gatsby” - Due: 2024-04-15</li>
              <li>Returned “1984” - On time</li>
              <li>Borrowed “To Kill a Mockingbird” - Due: 2024-04-20</li>
            </ul>
          </div>
        </main>
      </div>
    </div>
  )
}

export default StudentDashboard