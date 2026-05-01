import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './LibrarianDashboard.css'

const navSections = [
  {
    section: 'MAIN',
    items: [
      { id: 'overview', icon: '📊', title: 'Overview' },
      { id: 'issue-return', icon: '📖', title: 'Issue / Return Books' },
      { id: 'availability', icon: '🔍', title: 'Book Availability' },
      { id: 'overdue', icon: '⏰', title: 'Overdue Books', badge: '5' }
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
  'issue-return': 'Issue / Return Books',
  availability: 'Book Availability',
  overdue: 'Overdue Books',
  students: 'Student Records',
  search: 'Search Books',
  account: 'Change Password'
}

export function LibrarianDashboard() {
  const navigate = useNavigate()
  const [activePage, setActivePage] = useState('overview')
  const [books, setBooks] = useState([])
  const [loans, setLoans] = useState([])
  const [students, setStudents] = useState([])
  const [message, setMessage] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [issueForm, setIssueForm] = useState({ book_id: '', student_id: '' })
  const [returnLoanId, setReturnLoanId] = useState('')
  const [passwordForm, setPasswordForm] = useState({ old_password: '', new_password: '' })
  const [notifications, setNotifications] = useState([])
  const [showNotifications, setShowNotifications] = useState(false)
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)

  const addNotification = (text) => {
    const id = Date.now()
    setNotifications(prev => [...prev, { id, text, timestamp: new Date() }])
  }

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user_role')
    localStorage.removeItem('user_id')
    navigate('/login', { replace: true })
  }

  useEffect(() => {
    loadBooks()
    loadLoans()
    loadStudents()
  }, [])

  const stats = useMemo(
    () => [
      { label: 'Books', value: books.length, type: 'blue' },
      { label: 'Active Loans', value: loans.filter(l => !l.returned).length, type: 'green' },
      { label: 'Overdue', value: loans.filter(l => !l.returned && new Date(l.due_date) < new Date()).length, type: 'red' },
      { label: 'Students', value: students.length, type: 'purple' }
    ],
    [books, loans, students]
  )

  async function loadBooks() {
    try {
      const response = await fetch('/api/books')
      setBooks(await response.json())
    } catch {
      addNotification('Unable to load books.')
    }
  }

  async function loadLoans() {
    try {
      const response = await fetch('/api/loans')
      setLoans(await response.json())
    } catch {
      addNotification('Unable to load loans.')
    }
  }

  async function loadStudents() {
    try {
      const response = await fetch('/api/students')
      setStudents(await response.json())
    } catch {
      addNotification('Unable to load students.')
    }
  }

  async function handleIssueBook(event) {
    event.preventDefault()
    try {
      const response = await fetch('/api/loans/issue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          book_id: Number(issueForm.book_id),
          user_id: Number(issueForm.student_id)
        })
      })
      if (response.ok) {
        setIssueForm({ book_id: '', student_id: '' })
        await loadLoans()
        await loadBooks()
        addNotification('Book issued successfully.')
      } else {
        addNotification('Failed to issue book.')
      }
    } catch {
      addNotification('Error issuing book.')
    }
  }

  async function handleReturnBook(event) {
    event.preventDefault()
    try {
      const response = await fetch(`/api/loans/${returnLoanId}/return`, { method: 'POST' })
      if (response.ok) {
        setReturnLoanId('')
        await loadLoans()
        await loadBooks()
        addNotification('Book return recorded.')
      } else {
        addNotification('Failed to return book.')
      }
    } catch {
      addNotification('Error returning book.')
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
                <button className="btn btn-blue" type="button" onClick={() => setActivePage('issue-return')}>Issue Book</button>
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
            <div className="card-hdr"><div className="card-title">Issue Book to Student</div></div>
            <form className="admin-form" onSubmit={handleIssueBook}>
              <div className="frow">
                <div className="fgroup" style={{ flex: 1 }}>
                  <label>Book ID</label>
                  <input value={issueForm.book_id} onChange={(event) => setIssueForm({ ...issueForm, book_id: event.target.value })} placeholder="Book ID" />
                </div>
                <div className="fgroup" style={{ flex: 1 }}>
                  <label>Student ID</label>
                  <input value={issueForm.student_id} onChange={(event) => setIssueForm({ ...issueForm, student_id: event.target.value })} placeholder="Student ID" />
                </div>
              </div>
              <button className="btn btn-blue" type="submit">Issue Book</button>
            </form>
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
                {books.map((book) => (
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
      const overdueLoans = loans.filter(l => !l.returned && new Date(l.due_date) < new Date())
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
                {students.map((student) => {
                  const borrowedCount = loans.filter(l => l.user_id === student.user_id && !l.returned).length
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
      const filtered = books.filter(b =>
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
            <div className="frow">
              <div className="fgroup"><label>Current password</label><input type="password" value={passwordForm.old_password} onChange={(event) => setPasswordForm({ ...passwordForm, old_password: event.target.value })} placeholder="Current password" /></div>
              <div className="fgroup"><label>New password</label><input type="password" value={passwordForm.new_password} onChange={(event) => setPasswordForm({ ...passwordForm, new_password: event.target.value })} placeholder="New password" /></div>
            </div>
            <button className="btn btn-blue" type="submit">Save password</button>
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
    </div>
  )
}
