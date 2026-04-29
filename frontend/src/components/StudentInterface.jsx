import '../App.css'
import { useState, useEffect } from 'react'
import axios from 'axios'
import FinesCard from './FinesCard'

function StudentInterface({ user, onLogout }) {
  const [books, setBooks] = useState([])
  const [borrowings, setBorrowings] = useState([])
  const [studentProfile, setStudentProfile] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTab, setActiveTabState] = useState(() => {
    return localStorage.getItem('studentActiveTab') || 'Dashboard'
  })
  
  // Wrapper to persist activeTab to localStorage
  const setActiveTab = (tab) => {
    setActiveTabState(tab)
    localStorage.setItem('studentActiveTab', tab)
  }
  const [selectedGenre, setSelectedGenre] = useState('')
  const [wishlist, setWishlist] = useState([])
  const [settings, setSettings] = useState({ phone: '', address: '' })
  const [statusMessage, setStatusMessage] = useState('')
  const [showBackToTop, setShowBackToTop] = useState(false)
  const [theme, setTheme] = useState('dark')
  const [showSettingsModal, setShowSettingsModal] = useState(false)
  const [clock, setClock] = useState(new Date())

  const popularBooks = [
    { title: 'Sapiens' },
    { title: 'The Silent Patient' },
    { title: 'Dune' },
    { title: 'Atomic Habits' }
  ]

  const curatedLists = ['Weekend Reads', 'Start-up Skills', 'Bookmaking Explorer', 'Silent Study Hours']

  const newsItems = [
    { title: 'Author Talk: Tomorrow @ 2 PM', detail: 'Join our author event in the reading hall.' },
    { title: 'New Graphic Novel Collection', detail: 'Fresh comics and visual storytelling arrivals.' }
  ]

  const quickActions = [
    { label: 'Browse Catalog', action: () => setActiveTab('Catalog') },
    { label: 'View My Books', action: () => setActiveTab('My Books') },
    { label: 'Report Library', action: () => setStatusMessage('Library support request opened.') },
    { label: 'Contact Library', action: () => setStatusMessage('Contact form placeholder activated.') }
  ]

  const formattedClock = clock.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })

  useEffect(() => {
    fetchBooks()
    fetchBorrowings()
    fetchProfile()
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    const timer = setInterval(() => {
      setClock(new Date())
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  const authHeaders = () => {
    const token = localStorage.getItem('token') || localStorage.getItem('access_token')
    return token ? { Authorization: `Bearer ${token}` } : {}
  }

  const fetchBooks = async () => {
    try {
      const response = await axios.get('/student/books/search', { headers: authHeaders() })
      setBooks(response.data.books || [])
    } catch (error) {
      console.error('Error fetching books:', error.response?.status, error.response?.data || error.message)
    }
  }

  const fetchBorrowings = async () => {
    try {
      const response = await axios.get('/borrowings', { headers: authHeaders() })
      setBorrowings(response.data)
    } catch (error) {
      console.error('Error fetching borrowings:', error)
    }
  }

  const fetchProfile = async () => {
    try {
      const response = await axios.get('/student/profile', { headers: authHeaders() })
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
  const genreAnalytics = ['Fiction', 'Sci-Fi', 'Non-Fiction'].map((category) => {
    const count = categoryCounts[category] || 0
    const percent = Math.round((count / totalCategories) * 100)
    return {
      category,
      percent,
      count,
      displayWidth: Math.max(percent, count > 0 ? percent : 4)
    }
  })

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
    if (book.status !== 'available') {
      alert('This book is not available for borrowing')
      return
    }

    try {
      await axios.post(`/student/books/${book.isbn}/borrow`, {}, { headers: authHeaders() })
      setStatusMessage(`Borrowed "${book.title}" successfully.`)
      fetchBooks()
      fetchBorrowings()
    } catch (error) {
      setStatusMessage(error.response?.data?.message || 'Error borrowing book')
    }
  }

  const handleReturn = async (borrowing) => {
    try {
      await axios.post(`/borrowings/${borrowing.borrow_id}/return`, {}, { headers: authHeaders() })
      setStatusMessage(`Returned "${borrowing.book_title}" successfully.`)
      fetchBorrowings()
      fetchBooks()
    } catch (error) {
      setStatusMessage(error.response?.data?.message || 'Error returning book')
    }
  }

  const handleRenew = async (borrowing) => {
    try {
      const response = await axios.post(`/borrowings/${borrowing.borrow_id}/renew`, {}, { headers: authHeaders() })
      setStatusMessage(response.data.message)
      fetchBorrowings()
      fetchBooks()
    } catch (error) {
      setStatusMessage(error.response?.data?.message || 'Error renewing book')
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

  const handleTabChange = (nav) => {
    setActiveTab(nav)
  }

  return (
    <div className={`student-interface ${theme}`}>
      <header className="interface-header">
        <div className="brand-nav">
          <div className="branding">
            <div className="brand-mark">LIBRX</div>
            <div>
              <span className="brand-title">LIBRX</span>
              <span className="brand-subtitle">Student Portal</span>
            </div>
          </div>
          <nav className="top-nav" role="tablist">
            {['Dashboard', 'Catalog', 'My Books', 'History'].map((nav) => (
              <button
                type="button"
                key={nav}
                className={`top-nav-btn ${activeTab === nav ? 'active-tab' : ''}`}
                aria-pressed={activeTab === nav}
                role="tab"
                onClick={() => handleTabChange(nav)}
              >
                {nav}
              </button>
            ))}
          </nav>
        </div>
        <div className="header-search">
          <input
            type="text"
            placeholder="Search the library..."
            className="search-input header-search-input"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="header-actions">
          <div className="student-avatar">{userFirstName?.slice(0, 2).toUpperCase()}</div>
          <button className="logout-btn" onClick={onLogout}>Logout</button>
        </div>
      </header>

      {activeTab === 'Dashboard' && (
        <>
          <section className="dashboard-hero">
            <div className="hero-left">
              <h2>Good {greetingText}, {userFirstName}</h2>
              <p>Here's your library overview for today</p>
              <span className={`status-pill ${accountStatusClass}`}>✓ {accountStatus}</span>
            </div>
            <div className="hero-news-panel">
              <h4>Library News & Events</h4>
              {newsItems.map((item) => (
                <div key={item.title} className="news-item">
                  <strong>{item.title}</strong>
                  <p>{item.detail}</p>
                </div>
              ))}
            </div>
            <div className="hero-quick-actions">
              <h4>Quick Actions</h4>
              <div className="quick-actions-hero">
                {quickActions.map((action) => (
                  <button key={action.label} type="button" className="action-button-small" onClick={action.action}>
                    {action.label}
                  </button>
                ))}
              </div>
            </div>
          </section>

          <section className="stats-row">
            <div className="stat-card">
              <h4>TOTAL BORROWED</h4>
              <div className="stat-value">{borrowedBooks.length}</div>
              <p>{overdueBorrowings.length} overdue items</p>
            </div>
            <div className="stat-card">
              <h4>SAVED FOR LATER</h4>
              <div className="stat-value">{wishlist.length}</div>
              <p>Your reading list</p>
            </div>
            <div className="stat-card">
              <h4>BOOKS READ</h4>
              <div className="stat-value">{booksRead}</div>
              <p>This month</p>
            </div>
            <div className="stat-card">
              <h4>ACTIVE REQUESTS</h4>
              <div className="stat-value">{activeRequests}</div>
              <p>Pending approval</p>
            </div>
          </section>
        </>
      )}

      <section className="main-panels">
        <div key={activeTab} className="content-panel">
          {activeTab === 'Dashboard' && (
            <>
              <section className="dashboard-overview-grid">
                <div className="dashboard-left-column">
                  <div className="account-fines-card">
                    <FinesCard />
                  </div>

                  <div className="analytics-card">
                    <h3>Borrowing Analytics</h3>
                    {genreAnalytics.length > 0 ? (
                      <div className="analytics-chart">
                        {genreAnalytics.map((item) => (
                          <div key={item.category} className="analytics-column">
                            <div className="analytics-column-bar-wrap">
                              <div className="analytics-column-bar" style={{ height: `${Math.max(item.percent || 4, 8)}%` }} />
                            </div>
                            <span className="analytics-column-label">{item.category}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="analytics-placeholder">
                        <span className="placeholder-icon">📊</span>
                        <h4>No genre data yet</h4>
                        <p>Borrowing activity will populate this summary and help you discover your strongest reading areas.</p>
                      </div>
                    )}
                  </div>

                  <div className="reader-card">
                    <h3>Reader of the Month ⭐</h3>
                    <div className="reader-card-inner">
                      <div className="reader-avatar">{userFirstName?.slice(0, 2).toUpperCase()}</div>
                      <div>
                        <p className="reader-label">You could be here!</p>
                        <p className="reader-note">Browse more, borrow more, and climb the leaderboard.</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="dashboard-center-column">
                  <div className="center-content-card">
                    <div className="featured-collections-section">
                      <h3>Featured Collections</h3>
                      <p className="featured-subtitle">Popular Right Now</p>
                      <div className="featured-shelf">
                        {popularBooks.map((book, index) => (
                          <div key={book.title} className={`cover-placeholder-card color-${index}`}>
                            <div className="cover-placeholder-title">{book.title}</div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="curated-lists-section">
                      <h3>Curated Reading Lists</h3>
                      <div className="curated-pill-row">
                        {curatedLists.map((list) => (
                          <div key={list} className="curated-pill">
                            <span className="curated-icon">📖</span>
                            <span>{list}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="dashboard-right-column">
                  <div className="library-collections-card">
                    <div className="collections-header">
                      <h3>Your Library Collections</h3>
                      <button className="add-button" onClick={() => setActiveTab('Catalog')}>+ Add books</button>
                    </div>
                    {wishlist.length > 0 ? (
                      <ul className="collection-list">
                        {wishlist.slice(0, 8).map((book) => (
                          <li key={book.book_id}>{book.title}</li>
                        ))}
                      </ul>
                    ) : (
                      <div className="empty-collections">
                        <div className="empty-icon">📚</div>
                        <p>No books saved yet. Browse the catalog and save titles to your reading list.</p>
                      </div>
                    )}
                  </div>
                </div>
              </section>
            </>
          )}

          {activeTab === 'Catalog' && (
            <>
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
                      const inLibrary = book.status === 'available' || (typeof book.available_copies === 'number' && book.available_copies > 0)
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
                            <p className="return-date">ISBN: {book.isbn}</p>
                            <div className="cover-actions">
                              <button className="primary-btn" onClick={() => handleSaveForLater(book)}>
                                Save for Later
                              </button>
                              <button
                                className={inLibrary ? 'secondary-btn' : 'disabled-btn'}
                                onClick={() => handleBorrow(book)}
                                disabled={!inLibrary}
                              >
                                {inLibrary ? 'Borrow' : 'Not Available'}
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
                    {borrowedBooks.map((item) => {
                      const dueDate = item.due_date ? new Date(item.due_date) : null
                      const isOverdue = item.status === 'overdue' || (dueDate && dueDate < new Date())
                      const renewalCount = item.renewal_count || 0
                      const canRenew = item.status === 'borrowed' && !isOverdue && renewalCount < 3
                      return (
                        <div key={item.borrow_id} className="log-item">
                          <div>
                            <h4>{item.book_title}</h4>
                            <p>{item.category || 'General'} • {item.status}</p>
                            <p className="renewal-info">Renewals: {renewalCount}/3</p>
                          </div>
                          <div>
                            <p>{item.due_date ? `Due ${item.due_date}` : 'No date'}</p>
                            <div className="book-actions">
                              <button className="secondary-btn" onClick={() => handleReturn(item)}>
                                Return Book
                              </button>
                              <button
                                className={canRenew ? 'primary-btn' : 'disabled-btn'}
                                onClick={() => handleRenew(item)}
                                disabled={!canRenew}
                              >
                                Renew
                              </button>
                            </div>
                          </div>
                        </div>
                      )
                    })}
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
