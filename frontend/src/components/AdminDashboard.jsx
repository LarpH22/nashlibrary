import '../App.css'
import { useState, useEffect } from 'react'
import axios from 'axios'

function AdminDashboard({ user, onLogout }) {
  const [activePanel, setActivePanel] = useState('System Overview')
  const [books, setBooks] = useState([])
  const [borrowings, setBorrowings] = useState([])
  const [users, setUsers] = useState([])
  const [fines, setFines] = useState([])
  const menuItems = ['System Overview', 'User Management', 'Library Settings', 'Reports & Analytics', 'System Logs']

  useEffect(() => {
    fetchBooks()
    fetchBorrowings()
    fetchUsers()
    fetchFines()
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

  const fetchFines = async () => {
    try {
      const response = await axios.get('/fines')
      setFines(response.data)
    } catch (error) {
      console.error('Error fetching fines:', error)
    }
  }

  const panelContent = {
    'System Overview': 'Summary of library performance and system status.',
    'User Management': 'Manage admins, librarians, and student accounts.',
    'Library Settings': 'Configure library rules, fines, and working hours.',
    'Reports & Analytics': 'View crowd insights, borrowing trends, and reports.',
    'System Logs': 'Audit logs and security events.',
    'System Health': 'Monitor uptime, error rates, and server availability.'
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Admin Dashboard</h1>
        <div className="user-info">
          <span>Welcome, {user?.full_name || user?.username || 'Admin'}</span>
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
          {activePanel === 'System Overview' && (
            <>
              <h2>System Overview</h2>
              <p>{panelContent['System Overview']}</p>
              <div className="stats-grid">
                <div className="stat-card"><h4>Total Users</h4><p>{users.length}</p></div>
                <div className="stat-card"><h4>Active Librarians</h4><p>{users.filter((u) => u.role === 'librarian').length}</p></div>
                <div className="stat-card"><h4>Books Cataloged</h4><p>{books.length}</p></div>
                <div className="stat-card"><h4>Open Fines</h4><p>{fines.filter((f) => f.status === 'pending').length}</p></div>
              </div>
            </>
          )}

          {activePanel === 'User Management' && (
            <>
              <h2>User Management</h2>
              <p>{panelContent['User Management']}</p>
              <div className="table-card">
                <ul>
                  {users.length ? users.map((u) => (
                    <li key={u.user_id}>{u.full_name || u.email} ({u.role}) - {u.status}</li>
                  )) : <li>No users found</li>}
                </ul>
              </div>
            </>
          )}

          {activePanel === 'Library Settings' && (
            <>
              <h2>Library Settings</h2>
              <p>{panelContent['Library Settings']}</p>
              <div className="table-card">
                <p>Borrow limit: 5 books</p>
                <p>Fine per day: $0.50</p>
                <p>Operating hours: 8am - 8pm</p>
              </div>
            </>
          )}

          {activePanel === 'Reports & Analytics' && (
            <>
              <h2>Reports & Analytics</h2>
              <p>{panelContent['Reports & Analytics']}</p>
              <div className="table-card">
                <p>Monthly borrow rate: {borrowings.length} records</p>
                <p>Overdue count: {borrowings.filter((b) => b.status === 'borrowed').length}</p>
                <p>Fine records: {fines.length}</p>
              </div>
            </>
          )}

          {activePanel === 'System Logs' && (
            <>
              <h2>System Logs</h2>
              <p>{panelContent['System Logs']}</p>
              <div className="table-card">
                <ul>
                  <li>2026-03-30 10:00 - Admin logged in</li>
                  <li>2026-03-30 11:15 - Book added: 'Clean Code'</li>
                  <li>2026-03-30 12:30 - Loan renewed: user student1</li>
                </ul>
              </div>
            </>
          )}

          <div className="stats-grid">
            <div className="stat-card" onClick={() => setActivePanel('User Management')}>
              <h4>Total Users</h4>
              <p>{users.length}</p>
            </div>
            <div className="stat-card" onClick={() => setActivePanel('System Logs')}>
              <h4>Active Sessions</h4>
              <p>{borrowings.length}</p>
            </div>
            <div className="stat-card" onClick={() => setActivePanel('System Overview')}>
              <h4>System Health</h4>
              <p>{Math.floor((books.filter((book) => book.available_copies > 0).length / (books.length || 1)) * 100)}%</p>
            </div>
            <div className="stat-card" onClick={() => setActivePanel('Reports & Analytics')}>
              <h4>Open Fines</h4>
              <p>{fines.filter((f) => f.status === 'pending').length}</p>
            </div>
          </div>

          <div className="recent-activity">
            <h3>System Activity</h3>
            <ul>
              <li>New librarian account created</li>
              <li>System backup completed</li>
              <li>User role updated for John Doe</li>
              <li>Library hours updated</li>
            </ul>
          </div>
        </main>
      </div>
    </div>
  )
}

export default AdminDashboard