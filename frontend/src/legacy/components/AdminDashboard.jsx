import './AdminDashboard.css'
import { useState, useEffect } from 'react'
import axios from 'axios'

function AdminDashboard({ user, onLogout }) {
  const [activePanel, setActivePanelState] = useState(() => {
    return localStorage.getItem('adminActivePanel') || 'System Overview'
  })
  
  // Wrapper to persist activePanel to localStorage
  const setActivePanel = (panel) => {
    setActivePanelState(panel)
    localStorage.setItem('adminActivePanel', panel)
  }
  const [borrowings, setBorrowings] = useState([])
  const [users, setUsers] = useState([])
  const [fines, setFines] = useState([])
  const [pendingRegistrations, setPendingRegistrations] = useState([])
  const menuItems = ['System Overview', 'Registration Review', 'User Management', 'Library Settings', 'Reports & Analytics', 'System Logs']

  useEffect(() => {
    fetchBorrowings()
    fetchUsers()
    fetchFines()
    fetchPendingRegistrations()
  }, [])

  const fetchBorrowings = async () => {
    try {
      const response = await axios.get('/borrowings')
      setBorrowings(Array.isArray(response.data) ? response.data : [])
    } catch (error) {
      console.error('Error fetching borrowings:', error)
      setBorrowings([])
    }
  }

  const fetchUsers = async () => {
    try {
      const response = await axios.get('/users')
      setUsers(Array.isArray(response.data) ? response.data : [])
    } catch (error) {
      console.error('Error fetching users:', error)
      setUsers([])
    }
  }

  const fetchFines = async () => {
    try {
      const response = await axios.get('/fines')
      setFines(Array.isArray(response.data) ? response.data : [])
    } catch (error) {
      console.error('Error fetching fines:', error)
      setFines([])
    }
  }

  const fetchPendingRegistrations = async () => {
    try {
      const response = await axios.get('/admin/pending-registrations')
      setPendingRegistrations(Array.isArray(response.data) ? response.data : [])
    } catch (error) {
      console.error('Error fetching pending registrations:', error)
      setPendingRegistrations([])
    }
  }

  const handleUserStatusChange = async (userId, newStatus) => {
    try {
      await axios.put(`/users/${userId}/status`, { status: newStatus })
      alert(`User status updated to ${newStatus}`)
      fetchUsers()
    } catch (error) {
      alert(error.response?.data?.message || 'Error updating user')
    }
  }

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return
    try {
      await axios.delete(`/users/${userId}`)
      alert('User deleted successfully')
      fetchUsers()
    } catch (error) {
      alert(
        JSON.stringify(
          error.response?.data ||
          error.message ||
          'Error deleting user'
        )
      )
    }
  }

  const handlePayFine = async (fineId) => {
    try {
      await axios.post(`/fines/${fineId}/pay`, {})
      alert('Fine marked as paid')
      fetchFines()
    } catch (error) {
      alert(error.response?.data?.message || 'Error processing fine')
    }
  }

  const handleRegistrationReview = async (studentId, action, notes = '') => {
    try {
      await axios.post(`/admin/review-registration/${studentId}`, {
        action: action,
        notes: notes
      })
      alert(`Registration ${action}d successfully`)
      fetchPendingRegistrations()
    } catch (error) {
      alert(error.response?.data?.message || `Error ${action}ing registration`)
    }
  }

  const panelContent = {
    'System Overview': 'Summary of library performance and system status.',
    'Registration Review': 'Review and approve/reject student registration requests.',
    'User Management': 'Manage admins, librarians, and student accounts.',
    'Library Settings': 'Configure library rules, fines, and working hours.',
    'Reports & Analytics': 'View crowd insights, borrowing trends, and reports.',
    'System Logs': 'Audit logs and security events.',
    'System Health': 'Monitor uptime, error rates, and server availability.'
  }

  const borrowingsList = Array.isArray(borrowings) ? borrowings : []
  const usersList = Array.isArray(users) ? users : []
  const finesList = Array.isArray(fines) ? fines : []

  return (
    <div className="admin-dashboard-container">
      <header className="admin-dashboard-header">
        <h1>Admin Dashboard</h1>
        <div className="admin-user-info">
          <span>Welcome, {user?.full_name || user?.username || 'Admin'}</span>
          <button onClick={onLogout} className="admin-logout-btn logout-btn">Logout</button>
        </div>
      </header>
      <div className="admin-dashboard-content">
        <aside className="admin-sidebar">
          <h3>Menu</h3>
          <ul>
            {menuItems.map((item) => (
              <li key={item} onClick={() => setActivePanel(item)} className={`admin-menu-item ${activePanel === item ? 'active-menu' : ''}`}>
                {item}
              </li>
            ))}
          </ul>
        </aside>
        <main className="admin-main-content">
          {activePanel === 'System Overview' && (
            <>
              <h2>System Overview</h2>
              <p>{panelContent['System Overview']}</p>
              <div className="stats-grid">
                <div className="stat-card" onClick={() => setActivePanel('User Management')}>
                  <h4>TOTAL USERS</h4>
                  <p style={{fontSize: '2em'}}>{usersList.length}</p>
                </div>
                <div className="stat-card" onClick={() => setActivePanel('User Management')}>
                  <h4>ACTIVE SESSIONS</h4>
                  <p style={{fontSize: '2em'}}>{borrowingsList.length}</p>
                </div>
                <div className="stat-card">
                  <h4>SYSTEM HEALTH</h4>
                  <p style={{fontSize: '2em'}}>100%</p>
                </div>
                <div className="stat-card" onClick={() => setActivePanel('Reports & Analytics')}>
                  <h4>OPEN FINES</h4>
                  <p style={{fontSize: '2em'}}>{finesList.filter((f) => f.status === 'pending').length}</p>
                </div>
              </div>
            </>
          )}

          {activePanel === 'Registration Review' && (
            <>
              <h2>Registration Review</h2>
              <p>{panelContent['Registration Review']}</p>
              <div className="table-card">
                <div className="user-table">
                  {pendingRegistrations.length ? pendingRegistrations.map((student) => (
                    <div key={student.student_id} className="user-row">
                      <div className="user-info-cell">
                        <h4>{student.full_name}</h4>
                        <p>{student.email} • Student ID: {student.student_number}</p>
                        <p>Registered: {new Date(student.created_at).toLocaleDateString()}</p>
                        {student.registration_document && (
                          <p>
                            <a
                              href={`/admin/student-document/${student.student_id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="proof-link"
                            >
                              View Registration Document
                            </a>
                          </p>
                        )}
                      </div>
                      <div className="user-actions">
                        <button
                          className="primary-btn"
                          onClick={() => {
                            const notes = prompt('Optional approval notes:');
                            handleRegistrationReview(student.student_id, 'approve', notes || '');
                          }}
                        >
                          Approve
                        </button>
                        <button
                          className="danger-btn"
                          onClick={() => {
                            const notes = prompt('Rejection reason (required):');
                            if (notes && notes.trim()) {
                              handleRegistrationReview(student.student_id, 'reject', notes);
                            } else {
                              alert('Rejection reason is required');
                            }
                          }}
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                  )) : <p>No pending registrations</p>}
                </div>
              </div>
            </>
          )}

          {activePanel === 'User Management' && (
            <>
              <h2>User Management</h2>
              <p>{panelContent['User Management']}</p>
              <div className="table-card">
                <div className="user-table">
                  {usersList.length ? usersList.map((u) => (
                    <div key={u.user_id} className="user-row">
                      <div className="user-info-cell">
                        <h4>{u.full_name || u.email}</h4>
                        <p>{u.email} • <strong>{u.role}</strong> • {u.status}</p>
                        {u.proof_file && u.status === 'pending' && (
                          <p><a href={`/uploads/${u.proof_file}`} target="_blank" rel="noopener noreferrer" className="proof-link">View proof</a></p>
                        )}
                      </div>
                      <div className="user-actions">
                        {u.status === 'pending' ? (
                          <>
                            <button className="primary-btn" onClick={() => handleUserStatusChange(u.user_id, 'active')}>
                              Approve
                            </button>
                            <button className="danger-btn" onClick={() => handleUserStatusChange(u.user_id, 'inactive')}>
                              Reject
                            </button>
                          </>
                        ) : (
                          <select 
                            value={u.status}
                            onChange={(e) => handleUserStatusChange(u.user_id, e.target.value)}
                            className="status-select"
                          >
                            <option value="active">Activate</option>
                            <option value="inactive">Deactivate</option>
                            <option value="suspended">Suspend</option>
                          </select>
                        )}
                        <button 
                          className="danger-btn"
                          onClick={() => handleDeleteUser(u.user_id)}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  )) : <p>No users found</p>}
                </div>
              </div>
            </>
          )}

          {activePanel === 'Library Settings' && (
            <>
              <h2>Library Settings</h2>
              <p>{panelContent['Library Settings']}</p>
              <div className="settings-card">
                <div className="setting-item">
                  <label>Borrow Limit:</label>
                  <input type="number" defaultValue="5" className="setting-input" />
                  <button className="primary-btn">Update</button>
                </div>
                <div className="setting-item">
                  <label>Fine Per Day ($):</label>
                  <input type="number" defaultValue="0.50" step="0.01" className="setting-input" />
                  <button className="primary-btn">Update</button>
                </div>
                <div className="setting-item">
                  <label>Operating Hours:</label>
                  <input type="text" defaultValue="8am - 8pm" className="setting-input" />
                  <button className="primary-btn">Update</button>
                </div>
              </div>
            </>
          )}

          {activePanel === 'Reports & Analytics' && (
            <>
              <h2>Reports & Analytics</h2>
              <p>{panelContent['Reports & Analytics']}</p>
              <div className="analytics-section">
                <div className="analytics-card">
                  <h3>Monthly Borrowing Rate</h3>
                  <p style={{fontSize: '1.5em'}}>{borrowingsList.length} records</p>
                </div>
                <div className="analytics-card">
                  <h3>Overdue Books</h3>
                  <p style={{fontSize: '1.5em'}}>{borrowingsList.filter((b) => b.status === 'borrowed').length}</p>
                </div>
                <div className="analytics-card">
                  <h3>Fine Records</h3>
                  <p style={{fontSize: '1.5em'}}>{finesList.length}</p>
                </div>
                <div className="analytics-card">
                  <h3>Active Users</h3>
                  <p style={{fontSize: '1.5em'}}>{usersList.filter(u => u.status === 'active').length}</p>
                </div>
              </div>
              <div className="fines-section">
                <h3>Outstanding Fines</h3>
                {finesList.filter(f => f.status === 'pending').length > 0 ? (
                  <div className="fines-list">
                    {finesList.filter(f => f.status === 'pending').map((fine) => (
                      <div key={fine.fine_id} className="fine-item">
                        <div>
                          <p><strong>{fine.student_email}</strong></p>
                          <p>Amount: ${fine.amount}</p>
                        </div>
                        <button className="primary-btn" onClick={() => handlePayFine(fine.fine_id)}>
                          Mark as Paid
                        </button>
                      </div>
                    ))}
                  </div>
                ) : <p>No outstanding fines</p>}
              </div>
            </>
          )}

          {activePanel === 'System Logs' && (
            <>
              <h2>System Logs</h2>
              <p>{panelContent['System Logs']}</p>
              <div className="logs-card">
                <ul className="logs-list">
                  <li>2026-04-10 12:30 - Admin accessed user management</li>
                  <li>2026-04-10 12:15 - Book inventory updated</li>
                  <li>2026-04-10 11:45 - New student registered</li>
                  <li>2026-04-10 11:30 - Fine payment processed</li>
                  <li>2026-04-10 11:00 - Librarian account deactivated</li>
                </ul>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  )
}

export default AdminDashboard