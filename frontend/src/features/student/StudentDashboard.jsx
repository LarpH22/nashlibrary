import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './StudentDashboard.css'

const navSections = [
  {
    section: 'MAIN',
    items: [
      { id: 'overview', icon: '📊', title: 'Overview' },
      { id: 'books', icon: '📖', title: 'My Borrowed Books' },
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
  history: 'Borrowing History',
  profile: 'My Profile',
  password: 'Change Password'
}

export function StudentDashboard() {
  const navigate = useNavigate()
  const [activePage, setActivePage] = useState('overview')
  const [loans, setLoans] = useState([])
  const [profile, setProfile] = useState(null)
  const [message, setMessage] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [profileForm, setProfileForm] = useState({ full_name: '', email: '', phone: '' })
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
    loadLoans()
    loadProfile()
  }, [])

  const stats = useMemo(
    () => {
      const active = loans.filter(l => !l.returned).length
      const overdue = loans.filter(l => !l.returned && new Date(l.due_date) < new Date()).length
      const returned = loans.filter(l => l.returned).length
      return [
        { label: 'Borrowed', value: active, type: 'green' },
        { label: 'Overdue', value: overdue, type: 'red' },
        { label: 'Returned', value: returned, type: 'blue' },
        { label: 'Total Loans', value: loans.length, type: 'purple' }
      ]
    },
    [loans]
  )

  async function loadLoans() {
    try {
      const response = await fetch('/api/loans/student')
      setLoans(await response.json())
    } catch {
      addNotification('Unable to load your books.')
    }
  }

  async function loadProfile() {
    try {
      const response = await fetch('/api/students/profile')
      setProfile(await response.json())
      if (response.ok) {
        const data = await response.json()
        setProfileForm({
          full_name: data.full_name || data.name || '',
          email: data.email || '',
          phone: data.phone || ''
        })
      }
    } catch {
      addNotification('Unable to load profile.')
    }
  }

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
                <button className="btn btn-outline" type="button" onClick={() => setActivePage('history')}>Borrowing History</button>
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

    return null
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
          {renderPage()}
        </div>
      </div>
    </div>
  )
}
