import '../App.css'
import { useState, useEffect } from 'react'
import axios from 'axios'

function UserDashboard({ user, onLogout }) {
  const [activePanel, setActivePanel] = useState('Manage Books')
  const [books, setBooks] = useState([])
  const [borrowings, setBorrowings] = useState([])
  const [users, setUsers] = useState([])
  const [showAddBook, setShowAddBook] = useState(false)
  const [newBook, setNewBook] = useState({ title: '', author: '', category: '', total_copies: 1, isbn: '' })
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

  const handleAddBook = async (e) => {
    e.preventDefault()
    try {
      await axios.post('/books', {
        ...newBook,
        available_copies: newBook.total_copies,
        added_by: user?.user_id
      })
      alert('Book added successfully')
      setNewBook({ title: '', author: '', category: '', total_copies: 1, isbn: '' })
      setShowAddBook(false)
      fetchBooks()
    } catch (error) {
      alert(error.response?.data?.message || 'Error adding book')
    }
  }

  const handleProcessReturn = async (borrowingId) => {
    try {
      await axios.post(`/borrowings/${borrowingId}/return`, {})
      alert('Book return processed successfully')
      fetchBorrowings()
      fetchBooks()
    } catch (error) {
      alert(error.response?.data?.message || 'Error processing return')
    }
  }

  const handleApproveUser = async (userId) => {
    try {
      await axios.put(`/users/${userId}/status`, { status: 'active' })
      alert('User approved')
      fetchUsers()
    } catch (error) {
      alert(error.response?.data?.message || 'Error approving user')
    }
  }

  const handleDeleteBook = async (bookId) => {
    if (!window.confirm('Are you sure you want to delete this book?')) return
    try {
      await axios.delete(`/books/${bookId}`)
      alert('Book deleted successfully')
      fetchBooks()
    } catch (error) {
      alert(error.response?.data?.message || 'Error deleting book')
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
        <h1>User Dashboard</h1>
        <div className="user-info">
          <span>Welcome, {user?.full_name || user?.username || 'User'}</span>
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
              
              {!showAddBook ? (
                <button className="primary-btn" onClick={() => setShowAddBook(true)}>
                  + Add New Book
                </button>
              ) : (
                <form onSubmit={handleAddBook} className="add-book-form">
                  <h3>Add New Book</h3>
                  <input
                    type="text"
                    placeholder="Title"
                    value={newBook.title}
                    onChange={(e) => setNewBook({...newBook, title: e.target.value})}
                    required
                    className="form-input"
                  />
                  <input
                    type="text"
                    placeholder="Author"
                    value={newBook.author}
                    onChange={(e) => setNewBook({...newBook, author: e.target.value})}
                    required
                    className="form-input"
                  />
                  <input
                    type="text"
                    placeholder="ISBN"
                    value={newBook.isbn}
                    onChange={(e) => setNewBook({...newBook, isbn: e.target.value})}
                    className="form-input"
                  />
                  <input
                    type="text"
                    placeholder="Category"
                    value={newBook.category}
                    onChange={(e) => setNewBook({...newBook, category: e.target.value})}
                    className="form-input"
                  />
                  <input
                    type="number"
                    placeholder="Total Copies"
                    value={newBook.total_copies}
                    onChange={(e) => setNewBook({...newBook, total_copies: parseInt(e.target.value)})}
                    min="1"
                    required
                    className="form-input"
                  />
                  <button type="submit" className="primary-btn">Save Book</button>
                  <button type="button" className="secondary-btn" onClick={() => setShowAddBook(false)}>Cancel</button>
                </form>
              )}

              <div className="table-card">
                <h3>Available Books</h3>
                {books.length ? (
                  <div className="books-list">
                    {books.map((book) => (
                      <div key={book.book_id} className="book-item">
                        <div className="book-info">
                          <h4>{book.title}</h4>
                          <p><strong>Author:</strong> {book.author}</p>
                          <p><strong>Category:</strong> {book.category}</p>
                          <p><strong>Available:</strong> {book.available_copies}/{book.total_copies}</p>
                        </div>
                        <button className="danger-btn" onClick={() => handleDeleteBook(book.book_id)}>
                          Delete
                        </button>
                      </div>
                    ))}
                  </div>
                ) : <p>No books found</p>}
              </div>
            </>
          )}

          {activePanel === 'View Borrowings' && (
            <>
              <h2>View Borrowings</h2>
              <p>{panelContent['View Borrowings']}</p>
              <div className="borrowings-section">
                {borrowings.length ? (
                  <div className="borrowings-list">
                    {borrowings.map((item) => (
                      <div key={item.borrow_id} className="borrowing-item">
                        <div className="borrowing-info">
                          <h4>{item.book_title || 'Unknown book'}</h4>
                          <p><strong>Student:</strong> {item.student_email || 'Unknown'}</p>
                          <p><strong>Due Date:</strong> {item.due_date}</p>
                          <p><strong>Status:</strong> <span className={`status-${item.status}`}>{item.status}</span></p>
                        </div>
                        {item.status === 'borrowed' && (
                          <button className="primary-btn" onClick={() => handleProcessReturn(item.borrow_id)}>
                            Process Return
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                ) : <p>No borrowings found</p>}
              </div>
            </>
          )}

          {activePanel === 'Manage Users' && (
            <>
              <h2>Manage Users</h2>
              <p>{panelContent['Manage Users']}</p>
              <div className="users-section">
                {users.length ? (
                  <div className="users-list">
                    {users.map((u) => (
                      <div key={u.user_id} className="user-item">
                        <div className="user-info-cell">
                          <h4>{u.full_name || u.email}</h4>
                          <p>{u.email}</p>
                          <p><strong>Role:</strong> {u.role} • <strong>Status:</strong> {u.status}</p>
                        </div>
                        {u.role === 'student' && u.status === 'inactive' && (
                          <button className="primary-btn" onClick={() => handleApproveUser(u.user_id)}>
                            Approve
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                ) : <p>No users found</p>}
              </div>
            </>
          )}

          {activePanel === 'Reports' && (
            <>
              <h2>Reports</h2>
              <p>{panelContent['Reports']}</p>
              <div className="reports-section">
                <div className="report-card">
                  <h3>Total Books</h3>
                  <p style={{fontSize: '1.5em'}}>{books.length}</p>
                </div>
                <div className="report-card">
                  <h3>Active Borrowings</h3>
                  <p style={{fontSize: '1.5em'}}>{borrowings.filter(b => b.status === 'borrowed').length}</p>
                </div>
                <div className="report-card">
                  <h3>Total Members</h3>
                  <p style={{fontSize: '1.5em'}}>{users.filter(u => u.role === 'student').length}</p>
                </div>
                <div className="report-card">
                  <h3>Completed Transactions</h3>
                  <p style={{fontSize: '1.5em'}}>{borrowings.filter(b => b.status === 'returned').length}</p>
                </div>
              </div>
            </>
          )}

          {activePanel === 'Support' && (
            <>
              <h2>Support</h2>
              <p>{panelContent['Support']}</p>
              <div className="support-card">
                <p><strong>Email:</strong> support@nashlibrary.com</p>
                <p><strong>Direct line:</strong> +1 555 987 6543</p>
                <p><strong>Hours:</strong> Monday - Friday, 9am - 5pm</p>
              </div>
            </>
          )}

          <div className="stats-grid">
            <div className="stat-card" onClick={() => setActivePanel('Manage Books')}>
              <h4>Total Books</h4>
              <p style={{fontSize: '2em'}}>{books.length}</p>
            </div>
            <div className="stat-card" onClick={() => setActivePanel('View Borrowings')}>
              <h4>Books Borrowed</h4>
              <p style={{fontSize: '2em'}}>{borrowings.filter(b => b.status === 'borrowed').length}</p>
            </div>
            <div className="stat-card" onClick={() => setActivePanel('View Borrowings')}>
              <h4>Overdue Books</h4>
              <p style={{fontSize: '2em'}}>{borrowings.filter((r) => r.status === 'borrowed').length}</p>
            </div>
            <div className="stat-card" onClick={() => setActivePanel('Manage Users')}>
              <h4>Active Members</h4>
              <p style={{fontSize: '2em'}}>{users.filter(u => u.role === 'student').length}</p>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

export default UserDashboard
