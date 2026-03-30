import '../App.css'
import { useState, useEffect } from 'react'
import axios from 'axios'

function LibrarianDashboard({ user, onLogout }) {
  const [activePanel, setActivePanel] = useState('Manage Books')
  const [books, setBooks] = useState([])
  const [borrowings, setBorrowings] = useState([])
  const [users, setUsers] = useState([])
  const menuItems = ['Manage Books', 'View Borrowings', 'Manage Users', 'Reports', 'Support']

  useEffect(() => {
    fetchBooks()
    fetchBorrowings()
    fetchUsers()
  }, [])

  const fetchBooks = async () => {
    try {
      const response = await axios.get('/books')
      setBooks(response.data)
    } catch (error) {
      console.error('Error fetching books:', error)
    }
  }

  const fetchBorrowings = async () => {
    try {
      const response = await axios.get('/borrowings')
      setBorrowings(response.data)
    } catch (error) {
      console.error('Error fetching borrowings:', error)
    }
  }

  const fetchUsers = async () => {
    try {
      const response = await axios.get('/users')
      setUsers(response.data)
    } catch (error) {
      console.error('Error fetching users:', error)
    }
  }

  const panelContent = {
    'Manage Books': 'Add/edit/remove books. Filter by category and availability.',
    'View Borrowings': 'Track book checkouts, due dates, and overdue records.',
    'Manage Users': 'Approve students, handle user status and permissions.',
    'Reports': 'Generate activity, borrowings, and fine report summaries.',
    'Support': 'Reach out to admin support at support@nashlibrary.com.'
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Librarian Dashboard</h1>
        <div className="user-info">
          <span>Welcome, {user?.full_name || user?.username || 'Librarian'}</span>
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
          {activePanel === 'Manage Books' && (
            <>
              <h2>Manage Books</h2>
              <p>{panelContent['Manage Books']}</p>
              <div className="table-card">
                <ul>
                  {books.length ? books.map((book) => (
                    <li key={book.book_id}>
                      <strong>{book.title}</strong> by {book.author} - {book.available_copies}/{book.total_copies} available
                    </li>
                  )) : <li>No books found</li>}
                </ul>
              </div>
            </>
          )}

          {activePanel === 'View Borrowings' && (
            <>
              <h2>View Borrowings</h2>
              <p>{panelContent['View Borrowings']}</p>
              <div className="table-card">
                <ul>
                  {borrowings.length ? borrowings.map((item) => (
                    <li key={item.borrow_id}>
                      {item.student_email || 'Unknown'} borrowed <strong>{item.book_title || 'Unknown'}</strong> - Due: {item.due_date} ({item.status})
                    </li>
                  )) : <li>No borrowings found</li>}
                </ul>
              </div>
            </>
          )}

          {activePanel === 'Manage Users' && (
            <>
              <h2>Manage Users</h2>
              <p>{panelContent['Manage Users']}</p>
              <div className="table-card">
                <ul>
                  {users.length ? users.map((u) => (
                    <li key={u.user_id}>{u.full_name || u.email} ({u.role}) - {u.status}</li>
                  )) : <li>No users found</li>}
                </ul>
              </div>
            </>
          )}

          {activePanel === 'Reports' && (
            <>
              <h2>Reports</h2>
              <p>{panelContent['Reports']}</p>
              <div className="table-card">
                <p>Books count: {books.length}</p>
                <p>Borrowings count: {borrowings.length}</p>
                <p>Users count: {users.length}</p>
              </div>
            </>
          )}

          {activePanel === 'Support' && (
            <>
              <h2>Support</h2>
              <p>{panelContent['Support']}</p>
              <div className="table-card">
                <p>Email: support@nashlibrary.com</p>
                <p>Direct line: +1 555 987 6543</p>
              </div>
            </>
          )}

          <div className="stats-grid">
            <div className="stat-card" onClick={() => setActivePanel('Manage Books')}>
              <h4>Total Books</h4>
              <p>{books.length}</p>
            </div>
            <div className="stat-card" onClick={() => setActivePanel('View Borrowings')}>
              <h4>Books Borrowed</h4>
              <p>{borrowings.length}</p>
            </div>
            <div className="stat-card" onClick={() => setActivePanel('Reports')}>
              <h4>Overdue Books</h4>
              <p>{borrowings.filter((r) => r.status === 'borrowed').length}</p>
            </div>
            <div className="stat-card" onClick={() => setActivePanel('Manage Users')}>
              <h4>Active Members</h4>
              <p>{users.length}</p>
            </div>
          </div>

          <div className="recent-activity">
            <h3>Recent Transactions</h3>
            <ul>
              <li>John Doe borrowed "The Great Gatsby"</li>
              <li>Jane Smith returned "1984"</li>
              <li>New book added: "To Kill a Mockingbird"</li>
            </ul>
          </div>
        </main>
      </div>
    </div>
  )
}

export default LibrarianDashboard