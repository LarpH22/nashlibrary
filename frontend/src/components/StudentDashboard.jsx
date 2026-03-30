import '../App.css'

function StudentDashboard({ user, onLogout }) {
  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Student Dashboard</h1>
        <div className="user-info">
          <span>Welcome, {user?.username}</span>
          <button onClick={onLogout} className="logout-btn">Logout</button>
        </div>
      </header>
      <div className="dashboard-content">
        <div className="sidebar">
          <h3>Menu</h3>
          <ul>
            <li>Search Books</li>
            <li>My Borrowed Books</li>
            <li>Profile</li>
          </ul>
        </div>
        <main className="main-content">
          <h2>Dashboard Overview</h2>
          <div className="stats-grid">
            <div className="stat-card">
              <h4>Books Borrowed</h4>
              <p>3</p>
            </div>
            <div className="stat-card">
              <h4>Due Soon</h4>
              <p>1</p>
            </div>
            <div className="stat-card">
              <h4>Fines</h4>
              <p>$0.00</p>
            </div>
          </div>
          <div className="recent-activity">
            <h3>Recent Activity</h3>
            <ul>
              <li>Borrowed "The Great Gatsby" - Due: 2024-04-15</li>
              <li>Returned "1984" - On time</li>
              <li>Borrowed "To Kill a Mockingbird" - Due: 2024-04-20</li>
            </ul>
          </div>
        </main>
      </div>
    </div>
  )
}

export default StudentDashboard