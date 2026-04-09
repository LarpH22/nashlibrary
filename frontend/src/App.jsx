import './App.css'
import { useState, useEffect } from 'react'
import axios from 'axios'
import StudentInterface from './components/StudentInterface'
import LibrarianDashboard from './components/LibrarianDashboard'
import AdminDashboard from './components/AdminDashboard'

function App() {
  const [showAuth, setShowAuth] = useState(false)
  const [isLogin, setIsLogin] = useState(true)
  const [formData, setFormData] = useState({ username: '', full_name: '', email: '', password: '', phone: '', address: '', role: 'student', proof: null })
  const [message, setMessage] = useState('')
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [userRole, setUserRole] = useState('')
  const [user, setUser] = useState(null)
  const [statsData, setStatsData] = useState({ total_books: 0, available_books: 0, borrowed_books: 0, total_members: 0 })

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      fetchUser()
    }
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await axios.get('/stats')
      setStatsData(response.data)
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  const fetchUser = async () => {
    try {
      const response = await axios.get('/user')
      setUser(response.data)
      setUserRole(response.data.role)
      setIsAuthenticated(true)
    } catch (error) {
      localStorage.removeItem('token')
      setIsAuthenticated(false)
    }
  }

  const stats = [
    { title: 'Total Books', value: (statsData.total_books || 0).toLocaleString(), suffix: '+' },
    { title: 'Available Now', value: (statsData.available_books || 0).toLocaleString(), suffix: '' },
    { title: 'Borrowed', value: (statsData.borrowed_books || 0).toLocaleString(), suffix: '' },
    { title: 'Members', value: (statsData.total_members || 0).toLocaleString(), suffix: '+' }
  ]

  const features = [
    { icon: '📚', title: 'Wide Collection', desc: 'Thousands of titles across all genres and categories, updated regularly.' },
    { icon: '🔍', title: 'Easy Search', desc: 'Find exactly what you need with fast, accurate search and filter tools.' },
    { icon: '📋', title: 'Online Borrowing', desc: 'Borrow books and track due dates — all managed in one place.' }
  ]

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleFileChange = (e) => {
    setFormData({ ...formData, proof: e.target.files[0] })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setMessage('')
    try {
      if (isLogin) {
        const response = await axios.post('/login', { username: formData.username, password: formData.password })
        setMessage(response.data.message)
        if (response.status === 200 || response.status === 201) {
          localStorage.setItem('token', response.data.access_token)
          axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`
          setUserRole(response.data.role)
          setIsAuthenticated(true)
          await fetchUser()
          setShowAuth(false)
          setFormData({ username: '', full_name: '', email: '', password: '', phone: '', address: '', role: 'student', proof: null })
        }
      } else {
        const formPayload = new FormData()
        formPayload.append('full_name', formData.full_name)
        formPayload.append('email', formData.email)
        formPayload.append('password', formData.password)
        formPayload.append('phone', formData.phone)
        formPayload.append('address', formData.address)
        formPayload.append('role', formData.role)
        if (formData.role === 'student' && formData.proof) {
          formPayload.append('proof', formData.proof)
        }

        const response = await axios.post('/register', formPayload, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        setMessage(response.data.message)
        if (response.status === 201) {
          setShowAuth(false)
          setFormData({ username: '', full_name: '', email: '', password: '', phone: '', address: '', role: 'student', proof: null })
        }
      }
    } catch (error) {
      setMessage(error.response?.data?.message || 'An error occurred')
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    delete axios.defaults.headers.common['Authorization']
    setIsAuthenticated(false)
    setUserRole('')
    setUser(null)
  }

  if (isAuthenticated) {
    if (userRole === 'admin') return <AdminDashboard user={user} onLogout={handleLogout} />
    if (userRole === 'librarian') return <LibrarianDashboard user={user} onLogout={handleLogout} />
    return <StudentInterface user={user} onLogout={handleLogout} />
  }

  return (
    <div className="online-library-home">

      {/* ── HEADER ── */}
      <div className="header-top">
        <div className="top-header">
          <span>📞 +12 345 678 000</span>
          <span>✉️ support@nashlibrary.com</span>
        </div>
        <nav className="main-nav">
          <h1 className="brand">Nash<span>Library</span></h1>
          <ul className="nav-links">
            <li>Home</li>
            <li>Books</li>
            <li>Find Books</li>
            <li>About Us</li>
            <li>Contact</li>
            <li className="nav-cta" onClick={() => setShowAuth(true)}>Sign In</li>
          </ul>
        </nav>
      </div>

      {/* ── HERO ── */}
      <section className="hero-home">
        <div className="hero-bg" />
        <div className="hero-overlay" />
        <div className="hero-content">
          <div className="hero-eyebrow">
            <span className="hero-eyebrow-dot" />
            Digital Library System
          </div>
          <h1>
            Your Gateway to<br />
            <em>Knowledge</em> &amp; Stories
          </h1>
          <p>
            Explore thousands of books, borrow online, and manage your reading
            journey — all from one place.
          </p>
          <div className="hero-cta-wrap">
            <button className="primary-cta" onClick={() => setShowAuth(true)}>Get Started Free</button>
            <button className="secondary-cta">Browse Collection</button>
          </div>
        </div>
      </section>

      {/* ── STATS ── */}
      <section className="stats-section">
        {stats.map((s) => (
          <div className="stat-tile" key={s.title}>
            <p>{s.value}<span>{s.suffix}</span></p>
            <h4>{s.title}</h4>
          </div>
        ))}
      </section>

      {/* ── FEATURES ── */}
      <section className="features-section">
        {features.map((f) => (
          <div className="feature-card" key={f.title}>
            <div className="feature-icon">{f.icon}</div>
            <h3>{f.title}</h3>
            <p>{f.desc}</p>
          </div>
        ))}
      </section>

      {/* ── FOOTER ── */}
      <footer className="site-footer">
        <div className="footer-brand">Nash<span>Library</span></div>
        <span>© {new Date().getFullYear()} NashLibrary. All rights reserved.</span>
        <span>📞 +12 345 678 000 &nbsp;·&nbsp; ✉️ support@nashlibrary.com</span>
      </footer>

      {/* ── AUTH MODAL ── */}
      {showAuth && (
        <div className="auth-modal">
          <div className="auth-form">
            <h3>{isLogin ? 'Welcome Back' : 'Create Account'}</h3>
            <p className="auth-subtitle">
              {isLogin ? 'Sign in to access your library' : 'Join NashLibrary today — it\'s free'}
            </p>
            <form onSubmit={handleSubmit}>
              {isLogin ? (
                <input
                  type="text"
                  name="username"
                  placeholder="Username or Email"
                  value={formData.username}
                  onChange={handleInputChange}
                  required
                />
              ) : (
                <>
                  <input
                    type="text"
                    name="full_name"
                    placeholder="Full Name"
                    value={formData.full_name}
                    onChange={handleInputChange}
                    required
                  />
                  <input
                    type="email"
                    name="email"
                    placeholder="Email address"
                    value={formData.email}
                    onChange={handleInputChange}
                    required
                  />
                  <input
                    type="text"
                    name="phone"
                    placeholder="Phone Number"
                    value={formData.phone}
                    onChange={handleInputChange}
                    required
                  />
                  <input
                    type="text"
                    name="address"
                    placeholder="Address"
                    value={formData.address}
                    onChange={handleInputChange}
                    required
                  />
                  <select name="role" value={formData.role} onChange={handleInputChange} className="select-input">
                    <option value="student">Student</option>
                    <option value="user">General User</option>
                  </select>
                  {formData.role === 'student' && (
                    <div className="proof-upload">
                      <label htmlFor="proof">Proof of Enrollment</label>
                      <input
                        type="file"
                        name="proof"
                        id="proof"
                        accept=".pdf,.jpg,.jpeg,.png"
                        onChange={handleFileChange}
                        required
                      />
                    </div>
                  )}
                </>
              )}
              <input
                type="password"
                name="password"
                placeholder="Password"
                value={formData.password}
                onChange={handleInputChange}
                required
              />
              <button type="submit">{isLogin ? 'Sign In' : 'Create Account'}</button>
            </form>
            <p>
              {isLogin ? "Don't have an account?" : 'Already have an account?'}
              <button onClick={() => { setIsLogin(!isLogin); setMessage('') }} className="switch-auth">
                {isLogin ? ' Register' : ' Sign In'}
              </button>
            </p>
            {message && <p className="message">{message}</p>}
            <button onClick={() => setShowAuth(false)} className="close-auth">Cancel</button>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
