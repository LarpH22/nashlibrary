import '../App.css'
import { useState, useEffect } from 'react'
import axios from 'axios'
import FinesCard from './FinesCard'

function StudentInterface({ user, onLogout }) {
  const [books, setBooks] = useState([])
  const [borrowings, setBorrowings] = useState([])
  const [studentProfile, setStudentProfile] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTab, setActiveTab] = useState('Dashboard')
  const [selectedGenre, setSelectedGenre] = useState('')
  const [wishlist, setWishlist] = useState([])
  const [settings, setSettings] = useState({ phone: '', address: '' })
  const [statusMessage, setStatusMessage] = useState('')
  const [showBackToTop, setShowBackToTop] = useState(false)
  const [theme, setTheme] = useState('dark')
  const [showSettingsModal, setShowSettingsModal] = useState(false)

  useEffect(() => {
    fetchBooks()
    fetchBorrowings()
    fetchProfile()
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
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

  const fetchProfile = async () => {
    try {
      const response = await axios.get('/student/profile')
      setStudentProfile(response.data)
      setSettings({ phone: response.data.phone || '', address: response.data.address || '' })
    } catch (error) {
      console.error('Error fetching profile:', error)
    }
  }

  const studentBorrowings = borrowings.filter((item) => item.student_email === user?.email)
  const overdueBorrowings = studentBorrowings.filter((item) => {
    const dueDate = item.due_date ? new Date(item.due_date) : null
    return item.status === 'overdue' || (item.status === 'borrowed' && dueDate && dueDate < new Date())
  })
  const borrowedBooks = studentBorrowings.filter((item) => item.status === 'borrowed' || item.status === 'overdue')
  const accountStatus = overdueBorrowings.length > 0 ? 'On Hold' : 'Good Standing'
  const accountStatusClass = overdueBorrowings.length > 0 ? 'badge-hold' : 'badge-good'
  const isLibraryOpen = new Date().getHours() >= 8 && new Date().getHours() < 18
  const greetingText = (() => {
    const hour = new Date().getHours()
    if (hour < 12) return 'morning'
    if (hour < 18) return 'afternoon'
    return 'evening'
  })()
  const userFirstName = user?.full_name?.split(' ')[0] || 'Student'
  const booksRead = studentBorrowings.filter((item) => item.status === 'returned').length
  const activeRequests = studentBorrowings.filter((item) => item.status === 'pending').length

  const genres = Array.from(new Set(books.map((book) => book.category).filter(Boolean)))

  const filteredBooks = books.filter((book) => {
    const q = searchQuery.toLowerCase()
    const matchesQuery =
      book.title?.toLowerCase().includes(q) ||
      book.author?.toLowerCase().includes(q) ||
      book.category?.toLowerCase().includes(q) ||
      book.isbn?.toString().includes(q)

    const matchesGenre = selectedGenre ? book.category === selectedGenre : true
    return matchesQuery && matchesGenre
  })

  const searchSuggestions = books
    .filter((book) => {
      const q = searchQuery.toLowerCase()
      return q && (book.title?.toLowerCase().includes(q) || book.author?.toLowerCase().includes(q))
    })
    .slice(0, 5)

  const recentBooks = [...books].sort((a, b) => (b.book_id || 0) - (a.book_id || 0)).slice(0, 6)

  const categoryCounts = studentBorrowings.reduce((acc, item) => {
    const category = item.category || 'Other'
    acc[category] = (acc[category] || 0) + 1
    return acc
  }, {})
  const totalCategories = Object.values(categoryCounts).reduce((sum, value) => sum + value, 0) || 1
  const genreAnalytics = Object.entries(categoryCounts).map(([category, count]) => ({
    category,
    percent: Math.round((count / totalCategories) * 100)
  }))

  const topBorrowers = Array.from(
    borrowings.reduce((acc, item) => {
      const email = item.student_email || 'Unknown'
      acc.set(email, (acc.get(email) || 0) + 1)
      return acc
    }, new Map())
  )
    .map(([student_email, count]) => ({ student_email, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 4)

  const handleBorrow = async (book) => {
    if (book.available_copies <= 0) {
      alert('This book is not available for borrowing')
      return
    }
    try {
      await axios.post('/borrow', { book_id: book.book_id })
      setStatusMessage(`Borrowed "${book.title}" successfully.`)
      fetchBooks()
      fetchBorrowings()
    } catch (error) {
      setStatusMessage(error.response?.data?.message || 'Error borrowing book')
    }
  }

  const handleReturn = async (borrowing) => {
    try {
      await axios.post(`/borrowings/${borrowing.borrow_id}/return`, {})
      setStatusMessage(`Returned "${borrowing.book_title}" successfully.`)
      fetchBorrowings()
      fetchBooks()
    } catch (error) {
      setStatusMessage(error.response?.data?.message || 'Error returning book')
    }
  }

  const handleSaveForLater = (book) => {
    if (!wishlist.some((item) => item.book_id === book.book_id)) {
      setWishlist([...wishlist, book])
    }
  }

  const handleUpdateSettings = async (e) => {
    e.preventDefault()
    try {
      await axios.put('/student/profile', {
        phone: settings.phone,
        address: settings.address
      })
      setStatusMessage('Profile settings updated.')
      fetchProfile()
    } catch (error) {
      setStatusMessage(error.response?.data?.message || 'Error updating settings')
    }
  }

  const handleScroll = () => {
    setShowBackToTop(window.scrollY > 400)
  }

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark')
  }

  return (
    <div className={`student-interface ${theme}`}>
      <header className="interface-header">
        <div className="brand-nav">
          <div className="branding">
            <span className="brand-mark">LIBRX</span>
          </div>
          <nav className="top-nav">
            {['Dashboard', 'Catalog', 'My Books', 'History'].map((nav) => (
              <button
                key={nav}
                className={`top-nav-btn ${activeTab === nav ? 'active-tab' : ''}`}
                onClick={() => setActiveTab(nav)}
              >
                {nav}
              </button>
            ))}
          </nav>
        </div>
        <div className="header-actions">
          <button className="icon-btn">Notifications</button>
          <div className="user-badge">{userFirstName?.slice(0, 2).toUpperCase()}</div>
          <button className="logout-btn" onClick={onLogout} title="Logout">
            Logout
          </button>
        </div>
      </header>

      <section className="dashboard-hero">
        <div>
          <h2>Good {greetingText}, {userFirstName}</h2>
          <p>Here's your library overview for today</p>
        </div>
        <div className="hero-status">
          <span className={`status-pill ${accountStatusClass}`}>{accountStatus}</span>
          <span className={`status-pill ${isLibraryOpen ? 'open-pill' : 'closed-pill'}`}>
            {isLibraryOpen ? 'Library Open' : 'Library Closed · Opens 8:00 AM'}
          </span>
        </div>
      </section>

      <section className="stats-grid">
        <div className="stat-card">
          <h3>Total Borrowed</h3>
          <p>{studentBorrowings.length}</p>
          <span>{overdueBorrowings.length} overdue items</span>
        </div>
        <div className="stat-card">
          <h3>Saved for Later</h3>
          <p>{wishlist.length}</p>
          <span>Your reading list</span>
        </div>
        <div className="stat-card">
          <h3>Books Read</h3>
          <p>{booksRead}</p>
          <span>This month</span>
        </div>
        <div className="stat-card">
          <h3>Active Requests</h3>
          <p>{activeRequests}</p>
          <span>Pending approval</span>
        </div>
      </section>

      <FinesCard />

      <section className="main-panels">
        <aside className="side-panel">
          <div className="analytics-card">
            <h3>Borrowing Analytics</h3>
            {genreAnalytics.length > 0 ? (
              genreAnalytics.map((item) => (
                <div key={item.category} className="analytics-item">
                  <span>{item.category}</span>
                  <div className="analytics-bar-wrap">
                    <div className="analytics-bar" style={{ width: `${item.percent}%` }} />
                  </div>
                  <span>{item.percent}%</span>
                </div>
              ))
            ) : (
              <div className="analytics-placeholder">
                <span className="placeholder-icon">📊</span>
                <h4>No genre data yet</h4>
                <p>Borrowing activity will populate this summary and help you discover your strongest reading areas.</p>
              </div>
            )}
          </div>

          <div className="genres-card">
            <h3>Genres</h3>
            <div className="genre-pill-group">
              {genres.map((genre) => (
                <button
                  key={genre}
                  className={`genre-pill ${selectedGenre === genre ? 'active' : ''}`}
                  onClick={() => setSelectedGenre(selectedGenre === genre ? '' : genre)}
                >
                  #{genre}
                </button>
              ))}
            </div>
          </div>

          <div className="leaderboard-card">
            <h3>Reader of the Month</h3>
            <ul>
              {topBorrowers.map((item) => (
                <li key={item.student_email}>{item.student_email} — {item.count} borrows</li>
              ))}
            </ul>
          </div>

          <div className="edit-profile-card">
            <div className="profile-icon">{userFirstName?.slice(0, 2).toUpperCase()}</div>
            <div>
              <h3>{studentProfile?.full_name || userFirstName}</h3>
              <p>{studentProfile?.student_number ? `Student · ${studentProfile.student_number}` : 'Student · ID #0000'}</p>
              <button className="secondary-btn" onClick={() => setShowSettingsModal(true)}>Edit Profile</button>
            </div>
          </div>
        </aside>

        <div className="content-panel">
          {activeTab === 'Dashboard' && (
            <>
              <section className="search-panel">
                <div className="search-header">
                  <div>
                    <h2>Search Books</h2>
                    <p>Search author, title, or ISBN with smart suggestions.</p>
                  </div>
                  <div className="autocomplete-wrapper">
                    <input
                      type="text"
                      placeholder="Search by title, author, ISBN..."
                      className="search-input"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    {searchSuggestions.length > 0 && (
                      <div className="autocomplete-dropdown">
                        {searchSuggestions.map((book) => (
                          <div key={book.book_id} className="autocomplete-item" onClick={() => setSearchQuery(book.title)}>
                            <strong>{book.title}</strong> — {book.author}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <div className="search-tag-row">
                  <button className={`genre-pill ${selectedGenre === '' ? 'active' : ''}`} onClick={() => setSelectedGenre('')}>All</button>
                  {genres.slice(0, 5).map((genre) => (
                    <button
                      key={genre}
                      className={`genre-pill ${selectedGenre === genre ? 'active' : ''}`}
                      onClick={() => setSelectedGenre(selectedGenre === genre ? '' : genre)}
                    >
                      {genre}
                    </button>
                  ))}
                </div>

                <div className="new-arrivals-row">
                  <h3>Just Added</h3>
                  <div className="arrival-grid">
                    {recentBooks.length > 0 ? (
                      recentBooks.map((book) => (
                        <div key={book.book_id} className="arrival-card">
                          <div className="cover-placeholder">{book.title?.slice(0, 2).toUpperCase()}</div>
                          <h4>{book.title}</h4>
                          <p>{book.author}</p>
                        </div>
                      ))
                    ) : (
                      <div className="arrival-placeholder">
                        <p>No new arrivals yet.</p>
                        <button className="primary-btn" onClick={() => { setSearchQuery(''); setSelectedGenre('') }}>
                          Browse Full Catalog
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                <div className="sync-card">
                  <div>
                    <h4>Catalog syncing</h4>
                    <p>New titles will appear once the sync completes.</p>
                  </div>
                  <div className="sync-footer">
                    <span className="sync-dot active" />
                    <span>Syncing catalog...</span>
                  </div>
                </div>
              </section>

              <section className="reading-log-card">
                <div className="card-header">
                  <h3>Digital Portfolio</h3>
                  <p>Books you have borrowed, logged for reference.</p>
                </div>
                {studentBorrowings.length > 0 ? (
                  <div className="reading-log-list">
                    {studentBorrowings.map((item) => (
                      <div key={item.borrow_id} className="log-item">
                        <div>
                          <h4>{item.book_title}</h4>
                          <p>{item.category || 'General'} • {item.status}</p>
                        </div>
                        <div>
                          <p>{item.due_date ? `Return by ${item.due_date}` : 'No date'}</p>
                          <p>{item.status === 'borrowed' ? `Days remaining: ${Math.max(0, Math.ceil((new Date(item.due_date) - new Date()) / (1000 * 60 * 60 * 24)))}` : 'Returned'}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="empty-state">No borrowing history available yet.</p>
                )}
              </section>
            </>
          )}

          {activeTab === 'Catalog' && (
            <>
              <section className="search-panel">
                <div className="search-header">
                  <div>
                    <h2>Library Catalog</h2>
                    <p>Browse the full collection and filter by genre or availability.</p>
                  </div>
                  <div className="autocomplete-wrapper">
                    <input
                      type="text"
                      placeholder="Search by title, author, ISBN..."
                      className="search-input"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                </div>
              </section>
              <section className="books-grid-panel">
                {books.length === 0 ? (
                  <div className="browse-empty-state">
                    <h3>Catalog is still loading</h3>
                    <p>We don’t have any books to show yet, but you can keep exploring once the catalog is updated.</p>
                    <button className="primary-btn" onClick={() => { setSearchQuery(''); setSelectedGenre('') }}>
                      Browse Full Catalog
                    </button>
                  </div>
                ) : filteredBooks.length > 0 ? (
                  <div className="book-cover-grid">
                    {filteredBooks.map((book) => {
                      const inLibrary = book.available_copies > 0
                      return (
                        <div key={book.book_id} className="cover-card">
                          <div className="cover-art">{book.title?.slice(0, 2).toUpperCase()}</div>
                          <div className="cover-detail">
                            <h4>{book.title}</h4>
                            <p>{book.author}</p>
                            <div className="book-tags">
                              <span className={inLibrary ? 'status-pill in' : 'status-pill out'}>{inLibrary ? 'In Library' : 'Out on Loan'}</span>
                              <span className="status-pill">#{book.category}</span>
                            </div>
                            <p className="return-date">Expected Return: {inLibrary ? 'Available now' : 'N/A'}</p>
                            <div className="cover-actions">
                              <button className="primary-btn" onClick={() => handleSaveForLater(book)}>
                                Save for Later
                              </button>
                              <button
                                className={book.available_copies > 0 ? 'secondary-btn' : 'disabled-btn'}
                                onClick={() => handleBorrow(book)}
                                disabled={book.available_copies <= 0}
                              >
                                {book.available_copies > 0 ? 'Borrow' : 'Not Available'}
                              </button>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <p className="empty-state">No books found. Try clearing the search or selecting another genre.</p>
                )}
              </section>
            </>
          )}

          {activeTab === 'My Books' && (
            <>
              <section className="reading-log-card">
                <div className="card-header">
                  <h3>Currently Borrowed</h3>
                  <p>Manage your active loans and return due books.</p>
                </div>
                {borrowedBooks.length > 0 ? (
                  <div className="reading-log-list">
                    {borrowedBooks.map((item) => (
                      <div key={item.borrow_id} className="log-item">
                        <div>
                          <h4>{item.book_title}</h4>
                          <p>{item.category || 'General'} • {item.status}</p>
                        </div>
                        <div>
                          <p>{item.due_date ? `Due ${item.due_date}` : 'No date'}</p>
                          <button className="secondary-btn" onClick={() => handleReturn(item)}>
                            Return Book
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="empty-state">No active loans right now.</p>
                )}
              </section>

              <section className="save-later-section">
                <h3>Saved for Later</h3>
                <div className="save-later-grid">
                  {wishlist.length > 0 ? (
                    wishlist.map((book) => (
                      <div key={book.book_id} className="wishlist-card">
                        <p>{book.title}</p>
                        <span>{book.author}</span>
                      </div>
                    ))
                  ) : (
                    <p>No books saved yet.</p>
                  )}
                </div>
              </section>
            </>
          )}

          {activeTab === 'History' && (
            <section className="reading-log-card">
              <div className="card-header">
                <h3>Borrow History</h3>
                <p>Review past loans and your reading progress.</p>
              </div>
              {studentBorrowings.length > 0 ? (
                <div className="reading-log-list">
                  {studentBorrowings.map((item) => (
                    <div key={item.borrow_id} className="log-item">
                      <div>
                        <h4>{item.book_title}</h4>
                        <p>{item.category || 'General'} • {item.status}</p>
                      </div>
                      <div>
                        <p>{item.due_date ? `Due ${item.due_date}` : 'No date'}</p>
                        <p>{item.status === 'returned' ? 'Returned' : item.status}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="empty-state">No borrowing history available yet.</p>
              )}
            </section>
          )}
        </div>
      </section>

      <section className="save-later-section">
        <h3>Save for Later</h3>
        <div className="save-later-grid">
          {wishlist.length > 0 ? (
            wishlist.map((book) => (
              <div key={book.book_id} className="wishlist-card">
                <p>{book.title}</p>
                <span>{book.author}</span>
              </div>
            ))
          ) : (
            <p>No books saved yet.</p>
          )}
        </div>
      </section>

      {showSettingsModal && (
        <div className="modal-overlay">
          <div className="settings-modal">
            <div className="modal-header">
              <div>
                <h3>Profile Settings</h3>
                <p className="modal-note">Update address and contact details when needed.</p>
              </div>
              <button className="close-modal" onClick={() => setShowSettingsModal(false)}>&times;</button>
            </div>
            <form onSubmit={(e) => { handleUpdateSettings(e); setShowSettingsModal(false) }} className="modal-form">
              <label>
                City / Address
                <input
                  value={settings.address}
                  onChange={(e) => setSettings({ ...settings, address: e.target.value })}
                  placeholder="Enter your city or address"
                />
              </label>
              <label>
                Contact Number
                <input
                  value={settings.phone}
                  onChange={(e) => setSettings({ ...settings, phone: e.target.value })}
                  placeholder="Enter phone number"
                />
              </label>
              <div className="modal-actions">
                <button type="button" className="secondary-btn" onClick={() => setShowSettingsModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="primary-btn">
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showBackToTop && (
        <button className="back-to-top" onClick={scrollToTop}>Back to Top</button>
      )}

      {statusMessage && <div className="toast-message">{statusMessage}</div>}
    </div>
  )
}

export default StudentInterface
