import '../App.css'

function AdminDashboard({ user, onLogout }) {
  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Admin Dashboard</h1>
        <div className="user-info">
          <span>Welcome, {user?.username}</span>
          <button onClick={onLogout} className="logout-btn">Logout</button>
        </div>
      </header>
      <div className="dashboard-content">
        <div className="sidebar">
          <h3>Menu</h3>
          <ul>
            <li>System Overview</li>
            <li>User Management</li>
            <li>Library Settings</li>
            <li>Reports & Analytics</li>
            <li>System Logs</li>
          </ul>
        </div>
        <main className="main-content">
          <h2>System Administration</h2>
          <div className="stats-grid">
            <div className="stat-card">
              <h4>Total Users</h4>
              <p>500</p>
            </div>
            <div className="stat-card">
              <h4>Active Sessions</h4>
              <p>45</p>
            </div>
            <div className="stat-card">
              <h4>System Health</h4>
              <p>98%</p>
            </div>
            <div className="stat-card">
              <h4>Pending Approvals</h4>
              <p>5</p>
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