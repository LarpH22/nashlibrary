import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BookSearch } from '../books/BookSearch.jsx'
import { fetchMostBorrowedBooks } from '../books/bookService.js'
import './StudentDashboard.css'

const navSections = [
  {
    section: 'MAIN',
    items: [
      { id: 'overview', icon: '📊', title: 'Overview' },
      { id: 'books', icon: '📖', title: 'My Borrowed Books' },
      { id: 'popular', icon: '🔥', title: 'Top Books' },
      { id: 'catalog', icon: '🔍', title: 'Search Catalog' },
      { id: 'reading', icon: '📘', title: 'Reading History' },
      { id: 'history', icon: '📚', title: 'Borrowing History' }
    ]
  },
  {
    section: 'ACCOUNT',
    items: [
      { id: 'profile', icon: '👤', title: 'My Profile' },
      { id: 'password', icon: '🔑', title: 'Change Password' }
    ]
  }
]

const pageTitles = {
  overview: 'Overview',
  books: 'My Borrowed Books',
  popular: 'Top Books',
  catalog: 'Search Catalog',
  reading: 'Reading History',
  history: 'Borrowing History',
  profile: 'My Profile',
  password: 'Change Password'
}

export function StudentDashboard() {
  const navigate = useNavigate()
  const [activePage, setActivePage] = useState('overview')
  const [loans, setLoans] = useState([])
  const [profile, setProfile] = useState(null)
  const [popularBooks, setPopularBooks] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [profileForm, setProfileForm] = useState({ full_name: '', email: '', phone: '' })
  const [passwordForm, setPasswordForm] = useState({ old_password: '', new_password: '' })
  const [notifications, setNotifications] = useState([])
  const [showNotifications, setShowNotifications] = useState(false)
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)
  const [loading, setLoading] = useState(true)
  const [fetchError, setFetchError] = useState('')
  const [authStatus, setAuthStatus] = useState('pending')
  const [authMessage, setAuthMessage] = useState('')

  const addNotification = useCallback((text) => {
    const id = Date.now()
    setNotifications((prev) => [...prev, { id, text, timestamp: new Date() }])
  }, [])

  const getAuthToken = useCallback(() => {
    const token = localStorage.getItem('access_token') || localStorage.getItem('token')
    if (token) {
      return token
    }

    const cookies = document.cookie
      .split(';')
      .map((cookie) => cookie.trim())
      .reduce((acc, cookie) => {
        const [name, value] = cookie.split('=')
        if (name && value) {
          acc[name] = decodeURIComponent(value)
        }
        return acc
      }, {})
    return cookies['access_token'] || cookies['token'] || ''
  }, [])

  const decodeTokenRole = useCallback((token) => {
    if (!token || token.split('.').length !== 3) {
      return null
    }
    try {
      const payload = token.split('.')[1]
      const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
      const json = decodeURIComponent(decoded.split('').map((c) => `%${(`00${c.charCodeAt(0).toString(16)}`).slice(-2)}`).join(''))
      const parsed = JSON.parse(json)
      return parsed?.role || parsed?.user_role || null
    } catch (error) {
      console.warn('[StudentDashboard] decodeTokenRole failed', error)
      return null
    }
  }, [])

  const removeNotification = useCallback((id) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))
  }, [])

  const clearSession = useCallback(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_role')
    localStorage.removeItem('user_id')
  }, [])

  const redirectToLogin = useCallback(() => {
    clearSession()
    navigate('/login', { replace: true })
  }, [clearSession, navigate])

  const handleLogout = () => {
    clearSession()
    navigate('/login', { replace: true })
  }

  const loadLoans = useCallback(async () => {
    try {
      const token = getAuthToken()
      const response = await fetch('/api/loans/student', {
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        }
      })
      if (response.status === 401) {
        console.warn('[StudentDashboard] loadLoans unauthorized', response)
        redirectToLogin()
        return
      }
      const data = await response.json()
      console.log('[StudentDashboard] loadLoans response', response.status, data)
      if (!response.ok) {
        throw new Error(data?.message || 'Unable to load student loans')
      }
      setLoans(Array.isArray(data) ? data : [])
    } catch (err) {
      const message = err?.message || 'Unable to load your books.'
      console.error('[StudentDashboard] loadLoans error', err)
      setFetchError(message)
      addNotification(message)
    }
  }, [addNotification, getAuthToken, redirectToLogin])

  const loadProfile = useCallback(async () => {
    try {
      const token = getAuthToken()
      const response = await fetch('/api/students/profile', {
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        }
      })
      if (response.status === 401) {
        console.warn('[StudentDashboard] loadProfile unauthorized', response)
        redirectToLogin()
        return
      }
      const data = await response.json()
      console.log('[StudentDashboard] loadProfile response', response.status, data)
      if (!response.ok) {
        throw new Error(data?.message || 'Unable to load profile')
      }
      const role = data?.role || data?.user_role || localStorage.getItem('user_role')
      if (role && role !== 'student') {
        setAuthStatus('unauthorized')
        setAuthMessage('Unauthorized access. Login with a student account to continue.')
        console.warn('[StudentDashboard] profile role mismatch', { role, data })
        return
      }
      setProfile(data)
      setProfileForm({
        full_name: data.full_name || data.name || '',
        email: data.email || '',
        phone: data.phone || ''
      })
    } catch (err) {
      const message = err?.message || 'Unable to load profile.'
      console.error('[StudentDashboard] loadProfile error', err)
      setFetchError(message)
      addNotification(message)
    }
  }, [addNotification, getAuthToken, redirectToLogin])

  const loadPopularBooks = useCallback(async () => {
    try {
      const response = await fetchMostBorrowedBooks(5)
      setPopularBooks(Array.isArray(response?.books) ? response.books : [])
    } catch (err) {
      console.error('[StudentDashboard] loadPopularBooks error', err)
      addNotification('Unable to load the most borrowed books.')
    }
  }, [addNotification])

  useEffect(() => {
    const token = getAuthToken()
    const storedRole = localStorage.getItem('user_role')
    const tokenRole = decodeTokenRole(token)
    const role = storedRole || tokenRole

    if (!token) {
      console.warn('[StudentDashboard] missing token', { storedRole })
      redirectToLogin()
      return
    }

    if (role && role !== 'student') {
      console.warn('[StudentDashboard] wrong role', { role })
      setAuthStatus('unauthorized')
      setAuthMessage('Unauthorized access. Login with a student account to continue.')
      setLoading(false)
      return
    }

    setAuthStatus('authorized')
    setLoading(true)
    setFetchError('')
    Promise.allSettled([loadLoans(), loadProfile(), loadPopularBooks()]).finally(() => setLoading(false))
  }, [decodeTokenRole, getAuthToken, loadLoans, loadProfile, loadPopularBooks, redirectToLogin])

  const stats = useMemo(
    () => {
      const active = loans.filter(l => !l.returned).length
      const overdue = loans.filter(l => !l.returned && new Date(l.due_date) < new Date()).length
      const returned = loans.filter(l => l.returned).length
      const overdueRate = loans.length > 0 ? Math.round((overdue / loans.length) * 100) : 0
      return [
        { label: 'Borrowed', value: active, type: 'green' },
        { label: 'Overdue', value: overdue, type: 'red' },
        { label: 'Overdue Rate', value: `${overdueRate}%`, type: 'gold' },
        { label: 'Returned', value: returned, type: 'blue' },
        { label: 'Total Loans', value: loans.length, type: 'purple' }
      ]
    },
    [loans]
  )

  async function handleUpdateProfile(event) {
    event.preventDefault()
    try {
      const response = await fetch('/api/students/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profileForm)
      })
      if (response.ok) {
        await loadProfile()
        addNotification('Profile updated successfully.')
      } else {
        addNotification('Failed to update profile.')
      }
    } catch {
      addNotification('Error updating profile.')
    }
  }

  async function handleChangePassword(event) {
    event.preventDefault()
    try {
      const response = await fetch('/api/auth/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(passwordForm)
      })
      if (response.ok) {
        setPasswordForm({ old_password: '', new_password: '' })
        addNotification('Password changed successfully.')
      } else {
        addNotification('Password change failed.')
      }
    } catch {
      addNotification('Error changing password.')
    }
  }

  function renderPage() {
    if (activePage === 'overview') {
      return (
        <>
          <div className="grid4">
            {stats.map((stat) => (
              <div key={stat.label} className={`stat ${stat.type}`}>
                <div className="stat-label">{stat.label}</div>
                <div className="stat-num">{stat.value}</div>
                <div className="stat-sub">Total</div>
                <div className="stat-icon">
                  {stat.label === 'Borrowed' ? '📖' : stat.label === 'Overdue' ? '⏰' : stat.label === 'Returned' ? '✓' : '📚'}
                </div>
              </div>
            ))}
          </div>
          <div className="grid2">
            <div className="card">
              <div className="card-hdr"><div className="card-title">Welcome Back!</div></div>
              <p>View your borrowed books, track due dates, and manage your account from this dashboard.</p>
              <p style={{ marginTop: '12px', fontSize: '12px', color: 'var(--muted)' }}>Student ID: {profile?.user_id || '—'}</p>
            </div>
            <div className="card">
              <div className="card-hdr"><div className="card-title">Quick Actions</div></div>
              <div style={{ display: 'grid', gap: '10px' }}>
                <button className="btn btn-green" type="button" onClick={() => setActivePage('books')}>View My Books</button>
                <button className="btn btn-outline" type="button" onClick={() => setActivePage('reading')}>Reading History</button>
                <button className="btn btn-outline" type="button" onClick={() => setActivePage('profile')}>Edit Profile</button>
              </div>
            </div>
          </div>
          {loans.filter(l => !l.returned).length > 0 && (
            <div className="card">
              <div className="card-hdr"><div className="card-title">Current Loans</div></div>
              <div className="admin-table-container">
                <table>
                  <thead>
                    <tr><th>Book</th><th>Issued</th><th>Due Date</th><th>Status</th></tr>
                  </thead>
                  <tbody>
                    {loans.filter(l => !l.returned).slice(0, 5).map((loan) => {
                      const isOverdue = new Date(loan.due_date) < new Date()
                      return (
                        <tr key={loan.loan_id}>
                          <td>{loan.book_title || loan.book_id}</td>
                          <td>{new Date(loan.issue_date).toLocaleDateString()}</td>
                          <td>{new Date(loan.due_date).toLocaleDateString()}</td>
                          <td style={{ color: isOverdue ? 'var(--red)' : 'var(--green)' }}>
                            {isOverdue ? '⚠ Overdue' : '✓ On Time'}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )
    }

    if (activePage === 'books') {
      const borrowedLoans = loans.filter(l => !l.returned)
      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">My Borrowed Books ({borrowedLoans.length})</div></div>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr><th>Book Title</th><th>Issued Date</th><th>Due Date</th><th>Days Left</th><th>Status</th></tr>
              </thead>
              <tbody>
                {borrowedLoans.map((loan) => {
                  const daysLeft = Math.ceil((new Date(loan.due_date) - new Date()) / (1000 * 60 * 60 * 24))
                  const isOverdue = daysLeft < 0
                  return (
                    <tr key={loan.loan_id}>
                      <td>{loan.book_title || loan.book_id}</td>
                      <td>{new Date(loan.issue_date).toLocaleDateString()}</td>
                      <td>{new Date(loan.due_date).toLocaleDateString()}</td>
                      <td style={{ color: isOverdue ? 'var(--red)' : daysLeft < 3 ? 'var(--gold)' : 'var(--green)', fontWeight: 'bold' }}>
                        {isOverdue ? `${Math.abs(daysLeft)} days overdue` : `${daysLeft} days`}
                      </td>
                      <td>{isOverdue ? '⚠ Overdue' : daysLeft < 3 ? '⏰ Due Soon' : '✓ Active'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )
    }

    if (activePage === 'catalog') {
      return <BookSearch initialKeyword={searchQuery} />
    }

    if (activePage === 'reading') {
      const readingHistory = loans
      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">Reading History</div></div>
          <p>Review your student eLibrary history for all borrowed books, including active reads and completed returns.</p>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr>
                  <th>Book Title</th>
                  <th>Issued</th>
                  <th>Returned</th>
                  <th>Duration</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {readingHistory.length === 0 ? (
                  <tr><td colSpan="5" style={{ color: 'var(--muted)', padding: '18px', textAlign: 'center' }}>No reading history found yet.</td></tr>
                ) : (
                  readingHistory.map((loan) => {
                    const issuedDate = new Date(loan.issue_date)
                    const returnedDate = loan.return_date ? new Date(loan.return_date) : null
                    const durationDays = Math.ceil(((returnedDate || new Date()) - issuedDate) / (1000 * 60 * 60 * 24))
                    const isOverdue = !loan.returned && new Date(loan.due_date) < new Date()
                    return (
                      <tr key={loan.loan_id}>
                        <td>{loan.book_title || loan.book_id}</td>
                        <td>{issuedDate.toLocaleDateString()}</td>
                        <td>{returnedDate ? returnedDate.toLocaleDateString() : 'In progress'}</td>
                        <td>{durationDays} day{durationDays === 1 ? '' : 's'}</td>
                        <td style={{ color: loan.returned ? 'var(--blue)' : isOverdue ? 'var(--red)' : 'var(--green)' }}>
                          {loan.returned ? 'Returned' : isOverdue ? 'Overdue' : 'In progress'}
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )
    }

    if (activePage === 'popular') {
      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">Top Borrowed Books</div></div>
          <p>These are the most borrowed books in the system, with current availability status.</p>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Author</th>
                  <th>Borrowed</th>
                  <th>Availability</th>
                </tr>
              </thead>
              <tbody>
                {popularBooks.length === 0 ? (
                  <tr><td colSpan="4" style={{ color: 'var(--muted)', padding: '18px', textAlign: 'center' }}>No data available.</td></tr>
                ) : (
                  popularBooks.map((book) => (
                    <tr key={book.book_id || book.id}>
                      <td>{book.title}</td>
                      <td>{book.author}</td>
                      <td>{book.borrow_count ?? 0}</td>
                      <td style={{ color: book.status === 'borrowed' || book.available_copies === 0 ? 'var(--red)' : 'var(--green)' }}>
                        {book.status === 'borrowed' || book.available_copies === 0 ? 'Borrowed' : 'Available'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )
    }

    if (activePage === 'history') {
      const history = loans.filter(l => l.returned)
      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">Borrowing History ({history.length})</div></div>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr><th>Book Title</th><th>Issued</th><th>Returned</th><th>Duration</th></tr>
              </thead>
              <tbody>
                {history.map((loan) => {
                  const duration = Math.ceil((new Date(loan.return_date || loan.due_date) - new Date(loan.issue_date)) / (1000 * 60 * 60 * 24))
                  return (
                    <tr key={loan.loan_id}>
                      <td>{loan.book_title || loan.book_id}</td>
                      <td>{new Date(loan.issue_date).toLocaleDateString()}</td>
                      <td>{loan.return_date ? new Date(loan.return_date).toLocaleDateString() : '—'}</td>
                      <td>{duration} days</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )
    }

    if (activePage === 'profile') {
      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">My Profile</div></div>
          <form className="admin-form" style={{ flexDirection: 'column' }} onSubmit={handleUpdateProfile}>
            <div className="frow">
              <div className="fgroup">
                <label>Full Name</label>
                <input value={profileForm.full_name} onChange={(event) => setProfileForm({ ...profileForm, full_name: event.target.value })} placeholder="Full Name" />
              </div>
              <div className="fgroup">
                <label>Email</label>
                <input type="email" value={profileForm.email} onChange={(event) => setProfileForm({ ...profileForm, email: event.target.value })} placeholder="Email" />
              </div>
            </div>
            <div className="fgroup">
              <label>Phone (optional)</label>
              <input value={profileForm.phone} onChange={(event) => setProfileForm({ ...profileForm, phone: event.target.value })} placeholder="Phone" />
            </div>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button className="btn btn-green" type="submit">Save Changes</button>
              <button className="btn btn-outline" type="button" onClick={() => loadProfile()}>Cancel</button>
            </div>
          </form>
          {profile && (
            <div style={{ marginTop: '20px', paddingTop: '20px', borderTop: '1px solid var(--border)' }}>
              <h3 style={{ color: 'var(--text)', marginBottom: '12px' }}>Account Information</h3>
              <p><strong>Student ID:</strong> {profile.user_id || '—'}</p>
              <p><strong>Status:</strong> {profile.status || 'Active'}</p>
              <p><strong>Joined:</strong> {profile.created_at ? new Date(profile.created_at).toLocaleDateString() : '—'}</p>
            </div>
          )}
        </div>
      )
    }

    if (activePage === 'password') {
      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">Change Password</div></div>
          <form className="admin-form" style={{ flexDirection: 'column' }} onSubmit={handleChangePassword}>
            <div className="fgroup">
              <label>Current password</label>
              <input type="password" value={passwordForm.old_password} onChange={(event) => setPasswordForm({ ...passwordForm, old_password: event.target.value })} placeholder="Current password" />
            </div>
            <div className="fgroup">
              <label>New password</label>
              <input type="password" value={passwordForm.new_password} onChange={(event) => setPasswordForm({ ...passwordForm, new_password: event.target.value })} placeholder="New password" />
            </div>
            <button className="btn btn-green" type="submit">Save password</button>
          </form>
        </div>
      )
    }

    return (
      <div className="card">
        <div className="card-hdr"><div className="card-title">Page unavailable</div></div>
        <p>Unable to render this section. Please refresh or choose another page.</p>
      </div>
    )
  }

  return (
    <div className="student-dashboard-app">
      <div className="sidebar">
        <div className="logo">
          <div className="logo-icon">📚</div>
          <div className="logo-title">LibraX</div>
          <div className="logo-sub">Student</div>
        </div>
        <nav className="nav">
          {navSections.map((section) => (
            <div key={section.section}>
              <div className="nav-section">{section.section}</div>
              {section.items.map((item) => (
                <div key={item.id} className={`nav-item ${activePage === item.id ? 'active' : ''}`} onClick={() => setActivePage(item.id)}>
                  <span className="nav-icon">{item.icon}</span>
                  <span>{item.title}</span>
                  {item.badge && <span className="nav-badge">{item.badge}</span>}
                </div>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="avatar">ST</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '12px', color: 'var(--text)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {profile?.full_name || profile?.name || 'Student'}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--muted)' }}>{profile?.email || 'student@librax.edu'}</div>
            </div>
            <span style={{ cursor: 'pointer', fontSize: '14px', color: 'var(--red)' }} title="Logout" onClick={() => setShowLogoutConfirm(true)}>⏻</span>
          </div>
        </div>
      </div>
      {showLogoutConfirm && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 2000 }}>
          <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: '12px', padding: '24px', maxWidth: '400px', color: 'var(--text)' }}>
            <div style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px' }}>Confirm Logout</div>
            <div style={{ fontSize: '14px', color: 'var(--muted)', marginBottom: '24px' }}>Are you sure you want to log out?</div>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button onClick={() => setShowLogoutConfirm(false)} style={{ padding: '8px 16px', background: 'var(--bg3)', border: '1px solid var(--border)', color: 'var(--text)', borderRadius: '6px', cursor: 'pointer', fontSize: '13px' }}>Cancel</button>
              <button onClick={handleLogout} style={{ padding: '8px 16px', background: 'var(--red)', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', fontWeight: 500 }}>Logout</button>
            </div>
          </div>
        </div>
      )}
      <div className="main">
        <div className="topbar">
          <div className="page-title">{pageTitles[activePage] || 'Overview'}</div>
          <div className="search-wrap">
            <input className="search-input" value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder="Search..." />
          </div>
          <div style={{ position: 'relative' }}>
            <span style={{ fontSize: '18px', cursor: 'pointer', position: 'relative' }} onClick={() => setShowNotifications(!showNotifications)}>
              🔔
              {notifications.length > 0 && <span className="notif-badge">{notifications.length}</span>}
            </span>
            {showNotifications && (
              <div className="notif-panel">
                <div className="notif-header">Notifications</div>
                <div className="notif-list">
                  {notifications.length === 0 ? (
                    <div style={{ padding: '16px', textAlign: 'center', color: 'var(--muted)' }}>No notifications</div>
                  ) : (
                    notifications.map(notif => (
                      <div key={notif.id} className="notif-item">
                        <div className="notif-text">{notif.text}</div>
                        <button onClick={() => removeNotification(notif.id)} style={{ background: 'none', border: 'none', color: 'var(--muted)', cursor: 'pointer', fontSize: '12px' }}>✕</button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
          <div className="avatar">ST</div>
        </div>
        <div className="content">
          {authStatus === 'unauthorized' ? (
            <div className="card">
              <div className="card-hdr"><div className="card-title">Unauthorized access</div></div>
              <p>{authMessage || 'You do not have permission to view this dashboard.'}</p>
              <button className="btn btn-outline" type="button" onClick={handleLogout}>Go to Login</button>
            </div>
          ) : loading ? (
            <div className="card">
              <div className="card-hdr"><div className="card-title">Loading Dashboard</div></div>
              <p>Loading your student data. Please wait...</p>
            </div>
          ) : fetchError ? (
            <div className="card">
              <div className="card-hdr"><div className="card-title">Unable to load dashboard</div></div>
              <p>{fetchError}</p>
              <button className="btn btn-outline" type="button" onClick={() => {
                setLoading(true)
                setFetchError('')
                Promise.allSettled([loadLoans(), loadProfile()]).finally(() => setLoading(false))
              }}>Retry</button>
            </div>
          ) : (
            renderPage()
          )}
        </div>
      </div>
    </div>
  )
}
