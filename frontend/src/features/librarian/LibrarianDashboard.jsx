import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../shared/api.js'
import { clearStoredAuth } from '../../shared/authStorage.js'
import './LibrarianDashboard.css'

const baseNavSections = [
  {
    section: 'MAIN',
    items: [
      { id: 'overview', icon: '📊', title: 'Overview' },
      { id: 'issue-return', icon: '📖', title: 'Borrow Approvals' },
      { id: 'availability', icon: '🔍', title: 'Book Availability' },
      { id: 'overdue', icon: '⏰', title: 'Overdue Books' }
    ]
  },
  {
    section: 'RECORDS',
    items: [
      { id: 'students', icon: '👥', title: 'Student Records' },
      { id: 'search', icon: '🔎', title: 'Search Books' }
    ]
  },
  {
    section: 'ACCOUNT',
    items: [
      { id: 'account', icon: '🔑', title: 'Change Password' }
    ]
  }
]

const pageTitles = {
  overview: 'Overview',
  'issue-return': 'Borrow Approvals',
  availability: 'Book Availability',
  overdue: 'Overdue Books',
  students: 'Student Records',
  search: 'Search Books',
  account: 'Change Password'
}

const isLoanReturned = (loan) => loan.returned || String(loan.status || '').toLowerCase() === 'returned'

const isLoanOverdue = (loan) => {
  if (isLoanReturned(loan) || !loan.due_date) {
    return false
  }

  const dueDate = new Date(loan.due_date)
  return !Number.isNaN(dueDate.getTime()) && dueDate < new Date()
}

export function LibrarianDashboard() {
  const navigate = useNavigate()
  const [activePage, setActivePage] = useState('overview')
  const [books, setBooks] = useState([])
  const [loans, setLoans] = useState([])
  const [borrowRequests, setBorrowRequests] = useState([])
  const [students, setStudents] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [requestDueDates, setRequestDueDates] = useState({})
  const [returnLoanId, setReturnLoanId] = useState('')
  const [passwordForm, setPasswordForm] = useState({ old_password: '', new_password: '' })
  const [notifications, setNotifications] = useState([])
  const [showNotifications, setShowNotifications] = useState(false)
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [passwordError, setPasswordError] = useState('')

  const addNotification = (text) => {
    const id = Date.now()
    setNotifications(prev => [...prev, { id, text, timestamp: new Date() }])
  }

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }

  const safeBooks = useMemo(() => (Array.isArray(books) ? books : []), [books])
  const safeLoans = useMemo(() => (Array.isArray(loans) ? loans : []), [loans])
  const safeBorrowRequests = useMemo(() => (Array.isArray(borrowRequests) ? borrowRequests : []), [borrowRequests])
  const safeStudents = useMemo(() => (Array.isArray(students) ? students : []), [students])
  const pendingBorrowRequests = useMemo(() => safeBorrowRequests.filter((request) => request.status === 'pending'), [safeBorrowRequests])
  const overdueLoans = useMemo(() => safeLoans.filter(isLoanOverdue), [safeLoans])
  const navigationSections = useMemo(
    () => baseNavSections.map((section) => ({
      ...section,
      items: section.items.map((item) => (
        item.id === 'overdue'
          ? { ...item, badge: overdueLoans.length > 0 ? String(overdueLoans.length) : '' }
          : item
      ))
    })),
    [overdueLoans.length]
  )

  const studentRecords = useMemo(() => {
    const map = new Map()

    safeLoans.forEach((loan) => {
      const userId = loan.user_id ?? loan.student_id
      if (!userId) return

      const existing = map.get(userId) || {
        user_id: userId,
        full_name: loan.student_name || loan.full_name || 'Unknown',
        email: loan.student_email || '',
        status: loan.status || 'Active',
        borrowed_books: 0
      }

      map.set(userId, existing)
    })

    safeLoans.forEach((loan) => {
      const userId = loan.user_id ?? loan.student_id
      if (!userId) return
      const student = map.get(userId)
      if (student && !loan.returned) {
        student.borrowed_books = (student.borrowed_books || 0) + 1
      }
    })

    return Array.from(map.values())
  }, [safeLoans])

  const studentList = safeStudents.length > 0 ? safeStudents : studentRecords

  const handleLogout = () => {
    clearStoredAuth()
    navigate('/login', { replace: true })
  }

  const loadBooks = useCallback(async () => {
    try {
      const response = await api.get('/books/')
      setBooks(Array.isArray(response.data) ? response.data : [])
    } catch (error) {
      console.error('Unable to load books:', error)
      setBooks([])
      addNotification('Unable to load books.')
    }
  }, [])

  const loadLoans = useCallback(async () => {
    try {
      const response = await api.get('/api/admin/loans')
      setLoans(Array.isArray(response.data) ? response.data : [])
    } catch (error) {
      console.error('Unable to load loans:', error)
      setLoans([])
      addNotification('Unable to load loans.')
    }
  }, [])

  const loadStudents = useCallback(async () => {
    try {
      const response = await api.get('/api/admin/students')
      setStudents(Array.isArray(response.data) ? response.data : [])
    } catch (error) {
      console.error('Unable to load students:', error)
      setStudents([])
      addNotification('Unable to load students.')
    }
  }, [])

  const loadBorrowRequests = useCallback(async () => {
    try {
      const response = await api.get('/books/borrow-requests')
      setBorrowRequests(Array.isArray(response.data) ? response.data : [])
    } catch (error) {
      console.error('Unable to load borrow requests:', error)
      setBorrowRequests([])
      addNotification('Unable to load borrow requests.')
    }
  }, [])

  useEffect(() => {
    loadBooks()
    loadLoans()
    loadBorrowRequests()
    loadStudents()
  }, [loadBooks, loadLoans, loadBorrowRequests, loadStudents])

  const stats = useMemo(
    () => [
      { label: 'Books', value: safeBooks.length, type: 'blue' },
      { label: 'Pending Requests', value: pendingBorrowRequests.length, type: 'gold' },
      { label: 'Active Loans', value: safeLoans.filter(l => !isLoanReturned(l)).length, type: 'green' },
      { label: 'Overdue', value: overdueLoans.length, type: 'red' },
      { label: 'Students', value: studentList.length, type: 'purple' }
    ],
    [safeBooks, pendingBorrowRequests, safeLoans, overdueLoans.length, studentList]
  )

  async function handleApproveRequest(requestId) {
    const dueDate = requestDueDates[requestId]
    if (!dueDate) {
      addNotification('Set a due date before approving this request.')
      return
    }

    try {
      await api.post(`/books/borrow-requests/${requestId}/approve`, {
        due_date: dueDate
      })
      setRequestDueDates((prev) => {
        const next = { ...prev }
        delete next[requestId]
        return next
      })
      await Promise.allSettled([loadBorrowRequests(), loadLoans(), loadBooks()])
      addNotification('Borrow request approved.')
    } catch (error) {
      console.error('Error approving request:', error)
      await Promise.allSettled([loadBorrowRequests(), loadLoans(), loadBooks()])
      addNotification(error?.response?.data?.message || 'Failed to approve request.')
    }
  }

  async function handleRejectRequest(requestId) {
    try {
      await api.post(`/books/borrow-requests/${requestId}/reject`, {
        reason: 'Rejected by librarian'
      })
      await loadBorrowRequests()
      addNotification('Borrow request rejected.')
    } catch (error) {
      console.error('Error rejecting request:', error)
      await loadBorrowRequests()
      addNotification(error?.response?.data?.message || 'Failed to reject request.')
    }
  }

  async function handleReturnBook(event) {
    event.preventDefault()
    const loanId = Number(returnLoanId)
    if (!returnLoanId || Number.isNaN(loanId) || loanId <= 0) {
      addNotification('Please enter a valid Loan ID before returning a book.')
      return
    }

    try {
      await api.post('/books/return', { loan_id: loanId })
      setReturnLoanId('')
      await Promise.allSettled([loadBorrowRequests(), loadLoans(), loadBooks()])
      addNotification('Book return recorded.')
    } catch (error) {
      console.error('Error returning book:', error)
      await Promise.allSettled([loadLoans(), loadBooks()])
      addNotification(error?.response?.data?.message || 'Failed to return book.')
    }
  }

  async function handleChangePassword(event) {
    event.preventDefault()
    setPasswordError('')

    // Validate fields
    if (!passwordForm.old_password || !passwordForm.new_password) {
      setPasswordError('Both password fields are required.')
      return
    }

    if (passwordForm.new_password.length < 6) {
      setPasswordError('New password must be at least 6 characters long.')
      return
    }

    try {
      const response = await api.post('/api/admin/password', passwordForm)
      console.log('Password change response:', response.status, response.data)
      const successMessage = response.data?.message
      if (response.status === 200 && successMessage && successMessage.toLowerCase().includes('updated successfully')) {
        setPasswordForm({ old_password: '', new_password: '' })
        setPasswordError('')
        setShowPasswordModal(true)
      } else {
        const errorMsg = successMessage || 'Password change failed. Please try again.'
        console.warn('Password change did not succeed:', response.status, response.data)
        setPasswordError(errorMsg)
      }
    } catch (error) {
      console.error('Error changing password:', error.response?.status, error.response?.data)
      const errorMsg = error.response?.data?.message || error.message || 'Password change failed. Please try again.'
      setPasswordError(errorMsg)
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
                <div className="stat-sub">Current</div>
                <div className="stat-icon">
                  {stat.label === 'Books' ? '📚' : stat.label === 'Active Loans' ? '🔄' : stat.label === 'Overdue' ? '⏰' : '👥'}
                </div>
              </div>
            ))}
          </div>
          <div className="grid2">
            <div className="card">
              <div className="card-hdr"><div className="card-title">Overview</div></div>
              <p>Welcome to the Librarian Dashboard. You can issue and return books, check availability, and manage student records.</p>
            </div>
            <div className="card">
              <div className="card-hdr"><div className="card-title">Quick Actions</div></div>
              <div style={{ display: 'grid', gap: '10px' }}>
                <button className="btn btn-blue" type="button" onClick={() => setActivePage('issue-return')}>Review Requests</button>
                <button className="btn btn-outline" type="button" onClick={() => setActivePage('overdue')}>View Overdue</button>
                <button className="btn btn-outline" type="button" onClick={() => setActivePage('students')}>Student Records</button>
              </div>
            </div>
          </div>
        </>
      )
    }

    if (activePage === 'issue-return') {
      return (
        <>
          <div className="card">
            <div className="card-hdr"><div className="card-title">Pending Borrow Requests ({pendingBorrowRequests.length})</div></div>
            <div className="admin-table-container">
              <table>
                <thead>
                  <tr><th>Request</th><th>Student</th><th>Book</th><th>Requested</th><th>Due Date</th><th>Action</th></tr>
                </thead>
                <tbody>
                  {pendingBorrowRequests.length === 0 ? (
                    <tr><td colSpan="6" style={{ color: 'var(--muted)', textAlign: 'center', padding: '18px' }}>No pending borrow requests.</td></tr>
                  ) : (
                    pendingBorrowRequests.map((request) => (
                      <tr key={request.request_id}>
                        <td>{request.request_id}</td>
                        <td>{request.student_name || request.student_number || request.student_id}</td>
                        <td>{request.book_title || request.book_id}</td>
                        <td>{request.requested_at ? new Date(request.requested_at).toLocaleString() : ''}</td>
                        <td>
                          <input
                            className="table-date-input"
                            type="date"
                            value={requestDueDates[request.request_id] || ''}
                            onChange={(event) => setRequestDueDates({ ...requestDueDates, [request.request_id]: event.target.value })}
                          />
                        </td>
                        <td>
                          <div className="row-actions">
                            <button className="btn btn-green btn-sm" type="button" onClick={() => handleApproveRequest(request.request_id)}>Approve</button>
                            <button className="btn btn-outline btn-sm" type="button" onClick={() => handleRejectRequest(request.request_id)}>Reject</button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
          <div className="card">
            <div className="card-hdr"><div className="card-title">Return Book</div></div>
            <form className="admin-form" onSubmit={handleReturnBook}>
              <div className="fgroup" style={{ flex: 1 }}>
                <label>Loan ID</label>
                <input value={returnLoanId} onChange={(event) => setReturnLoanId(event.target.value)} placeholder="Loan ID" />
              </div>
              <button className="btn btn-blue" type="submit">Return Book</button>
            </form>
          </div>
        </>
      )
    }

    if (activePage === 'availability') {
      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">Book Availability</div></div>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr><th>Title</th><th>ISBN</th><th>Available</th><th>Total</th><th>Status</th></tr>
              </thead>
              <tbody>
                {safeBooks.map((book) => (
                  <tr key={book.book_id}>
                    <td>{book.title}</td>
                    <td>{book.isbn || '—'}</td>
                    <td>{book.available_copies || 0}</td>
                    <td>{book.total_copies || 0}</td>
                    <td>{(book.available_copies || 0) > 0 ? '✓ Available' : '✗ Out of Stock'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )
    }

    if (activePage === 'overdue') {
      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">Overdue Books ({overdueLoans.length})</div></div>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr><th>Loan ID</th><th>Book</th><th>Student</th><th>Due Date</th><th>Days Overdue</th></tr>
              </thead>
              <tbody>
                {overdueLoans.map((loan) => {
                  const daysOverdue = Math.floor((new Date() - new Date(loan.due_date)) / (1000 * 60 * 60 * 24))
                  return (
                    <tr key={loan.loan_id}>
                      <td>{loan.loan_id}</td>
                      <td>{loan.book_title || loan.book_id}</td>
                      <td>{loan.student_name || loan.user_id}</td>
                      <td>{new Date(loan.due_date).toLocaleDateString()}</td>
                      <td style={{ color: 'var(--red)', fontWeight: 'bold' }}>{daysOverdue} days</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )
    }

    if (activePage === 'students') {
      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">Student Records</div></div>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr><th>Student ID</th><th>Name</th><th>Email</th><th>Status</th><th>Books Borrowed</th></tr>
              </thead>
              <tbody>
                {studentList.map((student) => {
                  const borrowedCount = safeLoans.filter(l => l.user_id === student.user_id && !l.returned).length
                  return (
                    <tr key={student.user_id}>
                      <td>{student.user_id}</td>
                      <td>{student.full_name || student.name}</td>
                      <td>{student.email}</td>
                      <td>{student.status || 'Active'}</td>
                      <td>{borrowedCount}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )
    }

    if (activePage === 'search') {
      const filtered = safeBooks.filter(b =>
        b.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (b.author && b.author.toLowerCase().includes(searchQuery.toLowerCase()))
      )
      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">Search Books</div></div>
          <div style={{ marginBottom: '20px' }}>
            <input
              className="search-input"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search by title or author..."
            />
          </div>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr><th>Title</th><th>Author</th><th>ISBN</th><th>Available</th></tr>
              </thead>
              <tbody>
                {filtered.map((book) => (
                  <tr key={book.book_id}>
                    <td>{book.title}</td>
                    <td>{book.author || '—'}</td>
                    <td>{book.isbn || '—'}</td>
                    <td>{(book.available_copies || 0) > 0 ? 'Yes' : 'No'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )
    }

    if (activePage === 'account') {
      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">Change Password</div></div>
          <form className="admin-form" onSubmit={handleChangePassword}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%' }}>
              <div className="frow">
                <div className="fgroup"><label>Current password</label><input type="password" value={passwordForm.old_password} onChange={(event) => { setPasswordForm({ ...passwordForm, old_password: event.target.value }); setPasswordError(''); }} placeholder="Current password" /></div>
                <div className="fgroup"><label>New password</label><input type="password" value={passwordForm.new_password} onChange={(event) => { setPasswordForm({ ...passwordForm, new_password: event.target.value }); setPasswordError(''); }} placeholder="New password" /></div>
              </div>
              <button className="btn btn-blue" type="submit" style={{ alignSelf: 'flex-start' }}>Save password</button>
              {passwordError && <div className="password-error">{passwordError}</div>}
            </div>
          </form>
        </div>
      )
    }

    return null
  }

  return (
    <div className="librarian-dashboard-app">
      <div className="sidebar">
        <div className="logo">
          <div className="logo-icon">📚</div>
          <div className="logo-title">LibraX</div>
          <div className="logo-sub">Librarian</div>
        </div>
        <nav className="nav">
          {navigationSections.map((section) => (
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
            <div className="avatar">LI</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '12px', color: 'var(--text)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>Librarian</div>
              <div style={{ fontSize: '10px', color: 'var(--muted)' }}>librarian@librax.edu</div>
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
          <div className="avatar">LI</div>
        </div>
        <div className="content">
          {renderPage()}
        </div>
      </div>
      {showPasswordModal && (
        <div className="modal-overlay" onClick={() => setShowPasswordModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">Success</div>
            </div>
            <div className="modal-body">
              <div className="modal-message">Password changed successfully!</div>
            </div>
            <div className="modal-footer">
              <button className="btn-close" onClick={() => setShowPasswordModal(false)}>OK</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
