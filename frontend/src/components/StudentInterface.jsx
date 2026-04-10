import '../App.css'
import { useState, useEffect } from 'react'
import axios from 'axios'

function StudentInterface({ user, onLogout }) {
  const [books, setBooks] = useState([])
  const [borrowings, setBorrowings] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTab, setActiveTab] = useState('search')

  useEffect(() => {
    fetchBooks()
    fetchBorrowings()
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

  const filteredBooks = books.filter((book) => {
    const q = searchQuery.toLowerCase()
    return (
      book.title?.toLowerCase().includes(q) ||
      book.author?.toLowerCase().includes(q) ||
      book.category?.toLowerCase().includes(q) ||
      book.isbn?.toString().includes(q)
    )
  })

  const studentBorrowings = borrowings.filter((item) => item.student_email === user?.email)

  const handleBorrow = async (book) => {
    if (book.available_copies <= 0) {
      alert('This book is not available for borrowing')
      return
    }
    try {
      await axios.post('/borrow', {
        book_id: book.book_id,
        student_email: user?.email
      })
      alert(`Successfully borrowed "${book.title}"`)
      fetchBooks()
      fetchBorrowings()
    } catch (error) {
      alert(error.response?.data?.message || 'Error borrowing book')
    }
  }

  const handleReturn = async (borrowing) => {
    try {
      await axios.post(`/borrowings/${borrowing.borrow_id}/return`, {})
      alert('Book returned successfully')
      fetchBorrowings()
      fetchBooks()
    } catch (error) {
      alert(error.response?.data?.message || 'Error returning book')
    }
  }

  return (
    <div className="student-interface">
      <header className="interface-header">
        <h1>LIBRX</h1>
        <div className="header-right">
          <span>Welcome, {user?.full_name || 'Student'}</span>
          <button onClick={onLogout} className="logout-btn">Logout</button>
        </div>
      </header>

      <nav className="tab-nav">
        <button className={`tab-btn ${activeTab === 'search' ? 'active' : ''}`} onClick={() => setActiveTab('search')}>
          Search Books
        </button>
        <button className={`tab-btn ${activeTab === 'borrowed' ? 'active' : ''}`} onClick={() => setActiveTab('borrowed')}>
          My Borrowed Books ({studentBorrowings.length})
        </button>
      </nav>

      <div className="interface-content">
        {activeTab === 'search' && (
          <div className="search-section">
            <h2>Search Our Collection</h2>
            <div className="search-box">
              <input
                type="text"
                placeholder="Search by title, author, ISBN..."
                className="search-input"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="books-grid">
              {filteredBooks.length > 0 ? (
                filteredBooks.map((book) => (
                  <div key={book.book_id} className="book-card">
                    <h3>{book.title}</h3>
                    <p><strong>Author:</strong> {book.author}</p>
                    <p><strong>Category:</strong> {book.category}</p>
                    <p><strong>Available:</strong> {book.available_copies}/{book.total_copies}</p>
                    <button
                      className={book.available_copies > 0 ? 'primary-btn' : 'disabled-btn'}
                      onClick={() => handleBorrow(book)}
                      disabled={book.available_copies <= 0}
                    >
                      {book.available_copies > 0 ? 'Borrow' : 'Not Available'}
                    </button>
                  </div>
                ))
              ) : (
                <p>No books found matching your search.</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'borrowed' && (
          <div className="borrowed-section">
            <h2>My Borrowed Books</h2>
            {studentBorrowings.length > 0 ? (
              <div className="borrowed-list">
                {studentBorrowings.map((item) => (
                  <div key={item.borrow_id} className="borrowed-item">
                    <div className="borrowed-info">
                      <h3>{item.book_title || 'Unknown book'}</h3>
                      <p><strong>Due Date:</strong> {item.due_date}</p>
                      <p><strong>Status:</strong> {item.status}</p>
                    </div>
                    {item.status === 'borrowed' && (
                      <button className="primary-btn" onClick={() => handleReturn(item)}>
                        Return Book
                      </button>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p>You haven't borrowed any books yet.</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default StudentInterface
