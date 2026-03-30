import '../App.css'

function LibrarianDashboard({ user, onLogout }) {
  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Librarian Dashboard</h1>
        <div className="user-info">
          <span>Welcome, {user?.username}</span>
          <button onClick={onLogout} className="logout-btn">Logout</button>
        </div>
      </header>
      <div className="dashboard-content">
        <div className="sidebar">
          <h3>Menu</h3>
          <ul>
            <li>Manage Books</li>
            <li>View Borrowings</li>
            <li>Manage Users</li>
            <li>Reports</li>
          </ul>
        </div>
        <main className="main-content">
          <h2>Library Management</h2>
          <div className="stats-grid">
            <div className="stat-card">
              <h4>Total Books</h4>
              <p>1250</p>
            </div>
            <div className="stat-card">
              <h4>Books Borrowed</h4>
              <p>270</p>
            </div>
            <div className="stat-card">
              <h4>Overdue Books</h4>
              <p>12</p>
            </div>
            <div className="stat-card">
              <h4>Active Members</h4>
              <p>450</p>
            </div>
          </div>
          <div className="recent-activity">
            <h3>Recent Transactions</h3>
            <ul>
              <li>John Doe borrowed "The Great Gatsby"</li>
              <li>Jane Smith returned "1984"</li>
              <li>New book added: "To Kill a Mockingbird"</li>
            </ul>
          </div>
        </main>
      </div>
    </div>
  )
}

export default LibrarianDashboard