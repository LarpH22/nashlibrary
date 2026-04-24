import './App.css'
import { useState, useEffect } from 'react'
import axios from 'axios'
import { Search, Users, ClipboardList, Bell } from 'lucide-react'

import StudentInterface from './components/StudentInterface'
import LibrarianDashboard from './components/LibrarianDashboard'
import AdminDashboard from './components/AdminDashboard'

function App() {
  const [showAuth, setShowAuth] = useState(false)
  const [isLogin, setIsLogin] = useState(true)

  const [formData, setFormData] = useState({
    username: '',
    full_name: '',
    email: '',
    password: '',
    phone: '',
    address: '',
    role: 'student',
    proof: null
  })

  const [message, setMessage] = useState('')
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [showDashboard, setShowDashboard] = useState(false)
  const [userRole, setUserRole] = useState('')
  const [user, setUser] = useState(null)

  const [statsData, setStatsData] = useState({
    total_books: 0,
    available_books: 0,
    borrowed_books: 0,
    total_members: 0
  })

  const headerLinks = [
    { label: 'Home', target: 'home' },
    { label: 'Books', target: 'books' },
    { label: 'Find Books', target: 'books' },
    { label: 'About Us', target: 'about-us' },
    { label: 'Contact', target: 'contact' }
  ]

  const handleScrollToSection = (target) => {
    document.getElementById(target)?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    const token =
      localStorage.getItem('token') ||
      localStorage.getItem('access_token')

    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      fetchUser()
    }

    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const res = await axios.get('/stats')
      setStatsData(res.data)
    } catch (err) {
      console.error('Stats error:', err)
    }
  }

  const fetchUser = async () => {
    try {
      const res = await axios.get('/user')
      setUser(res.data)
      setUserRole(res.data.role)
      setIsAuthenticated(true)
    } catch (err) {
      localStorage.removeItem('token')
      localStorage.removeItem('access_token')
      delete axios.defaults.headers.common['Authorization']
      setIsAuthenticated(false)
    }
  }

  const stats = [
    { title: 'Total Books', value: statsData.total_books.toLocaleString(), suffix: '+' },
    { title: 'Available Now', value: statsData.available_books.toLocaleString(), suffix: '' },
    { title: 'Borrowed', value: statsData.borrowed_books.toLocaleString(), suffix: '' },
    { title: 'Members', value: statsData.total_members.toLocaleString(), suffix: '+' }
  ]

  const features = [
    { icon: <Search size={24} />, title: 'Easy Book Search', desc: 'Quickly find books using smart filters.' },
    { icon: <Users size={24} />, title: 'User Management', desc: 'Separate access for admins, librarians, and students.' },
    { icon: <ClipboardList size={24} />, title: 'Borrow Tracking', desc: 'Monitor borrowed and returned books with ease.' },
    { icon: <Bell size={24} />, title: 'Notifications', desc: 'Get updates for due dates and availability.' }
  ]

  const handleInputChange = (e) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const handleFileChange = (e) => {
    setFormData((prev) => ({
      ...prev,
      proof: e.target.files?.[0] || null
    }))
  }

  const resetForm = () => {
    setFormData({
      username: '',
      full_name: '',
      email: '',
      password: '',
      phone: '',
      address: '',
      role: 'student',
      proof: null
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setMessage('')

    try {
      if (isLogin) {
        const res = await axios.post('/login', {
          username: formData.username,
          password: formData.password
        })

        const token = res.data.access_token

        localStorage.setItem('token', token)
        localStorage.setItem('access_token', token)
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`

        setUserRole(res.data.role)
        setIsAuthenticated(true)
        setShowDashboard(true)

        await fetchUser()

        setShowAuth(false)
        resetForm()
      } else {
        const data = new FormData()

        Object.entries(formData).forEach(([key, value]) => {
          if (key !== 'proof') data.append(key, value)
        })

        if (formData.role === 'student' && formData.proof) {
          data.append('proof', formData.proof)
        }

        const res = await axios.post('/register', data, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })

        setMessage(res.data.message)

        if (res.status === 201) {
          setShowAuth(false)
          resetForm()
        }
      }
    } catch (err) {
      setMessage(err.response?.data?.message || 'Something went wrong')
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('access_token')
    delete axios.defaults.headers.common['Authorization']

    setIsAuthenticated(false)
    setShowDashboard(false)
    setUserRole('')
    setUser(null)
  }

  if (isAuthenticated && showDashboard) {
    if (userRole === 'admin') return <AdminDashboard user={user} onLogout={handleLogout} />
    if (userRole === 'librarian') return <LibrarianDashboard user={user} onLogout={handleLogout} />
    return <StudentInterface user={user} onLogout={handleLogout} />
  }

  return (
    <div className="online-library-home">

      <header className="site-header">
        <div className="brand-area">
          <div className="brand-mark">📚</div>
          <div className="brand-copy">
            <span className="brand-name">Nash Library</span>
            <span className="brand-tag">Access books anytime, anywhere</span>
          </div>
        </div>

        <nav className="site-nav">
          <ul className="nav-links">
            {headerLinks.map((link) => (
              <li key={link.target}>
                <button
                  type="button"
                  className="nav-link"
                  onClick={() => handleScrollToSection(link.target)}
                >
                  {link.label}
                </button>
              </li>
            ))}
          </ul>
        </nav>

        <div className="auth-actions">
          {isAuthenticated ? (
            <>
              <button type="button" className="secondary-btn" onClick={() => setShowDashboard(true)}>
                Go to Dashboard
              </button>
              <button type="button" className="secondary-btn" onClick={handleLogout}>
                Logout
              </button>
            </>
          ) : (
            <>
              <button type="button" className="secondary-btn" onClick={() => { setIsLogin(true); setShowAuth(true) }}>
                Login
              </button>
              <button type="button" className="primary-btn" onClick={() => { setIsLogin(false); setShowAuth(true) }}>
                Sign Up
              </button>
            </>
          )}
        </div>
      </header>

      <main>
        <section id="home" className="hero-section">
          <div className="hero-card">
            <div className="hero-copy">
              <h1>Access Knowledge Anytime, Anywhere</h1>
              <p>Search, borrow, and manage books in one modern platform built for students, librarians, and admins.</p>
              <div className="hero-actions">
                <button type="button" className="primary-btn" onClick={() => setShowAuth(true)}>Get Started</button>
                <button type="button" className="secondary-btn" onClick={() => handleScrollToSection('books')}>Explore Books</button>
              </div>
            </div>
            <div className="hero-visual">
              <div className="hero-shape" />
              <div className="book-stack">
                <div className="stack-card card-1" />
                <div className="stack-card card-2" />
                <div className="stack-card card-3" />
                <div className="stack-card card-4" />
              </div>
            </div>
          </div>
        </section>

        <section id="about-us" className="features-section">
          <div className="section-head">
            <div>
              <p className="section-label">What we offer</p>
              <h2>Library tools built for modern learning</h2>
            </div>
          </div>

          <div className="feature-grid">
            {features.map((f) => (
              <div className="feature-card" key={f.title}>
                <div className="feature-icon">{f.icon}</div>
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="books" className="stats-section">
          <div className="section-head">
            <div>
              <p className="section-label">Library metrics</p>
              <h2>Instant insight into your collection</h2>
            </div>
          </div>

          <div className="stats-grid">
            {stats.map((s) => (
              <div className="stat-tile" key={s.title}>
                <p>{s.value}<span>{s.suffix}</span></p>
                <h4>{s.title}</h4>
              </div>
            ))}
          </div>
        </section>

        <footer id="contact" className="site-footer">
          © {new Date().getFullYear()} Nash Library
        </footer>
      </main>

      {showAuth && (
        <div className="auth-modal">
          <div className="auth-form">
            <h3>{isLogin ? 'Login' : 'Register'}</h3>

            <form onSubmit={handleSubmit}>
              {isLogin ? (
                <>
                  <label>
                    Email or Username
                    <input
                      name="username"
                      placeholder="Email or full name"
                      onChange={handleInputChange}
                      required
                    />
                  </label>

                  <label>
                    Password
                    <input
                      name="password"
                      type="password"
                      placeholder="Enter your password"
                      onChange={handleInputChange}
                      required
                    />
                  </label>
                </>
              ) : (
                <>
                  <label>
                    Full Name
                    <input
                      name="full_name"
                      placeholder="Enter your full name"
                      onChange={handleInputChange}
                      required
                    />
                  </label>

                  <label>
                    Email
                    <input
                      name="email"
                      type="email"
                      placeholder="Enter your email"
                      onChange={handleInputChange}
                      required
                    />
                  </label>

                  <label>
                    Password
                    <input
                      name="password"
                      type="password"
                      placeholder="Enter your password"
                      onChange={handleInputChange}
                      required
                    />
                  </label>

                  <label>
                    Phone
                    <input
                      name="phone"
                      type="tel"
                      placeholder="Enter your phone"
                      onChange={handleInputChange}
                      required
                    />
                  </label>

                  <label>
                    Address
                    <input
                      name="address"
                      placeholder="Enter your address"
                      onChange={handleInputChange}
                      required
                    />
                  </label>

                  <label>
                    Role
                    <select name="role" value={formData.role} onChange={handleInputChange}>
                      <option value="student">Student</option>
                      <option value="user">User</option>
                    </select>
                  </label>
                </>
              )}

              <div className="auth-actions-row">
                <button type="submit" className="primary-btn">
                  {isLogin ? 'Login' : 'Register'}
                </button>
                <button type="button" className="secondary-btn" onClick={() => setIsLogin(!isLogin)}>
                  {isLogin ? 'Switch to Register' : 'Switch to Login'}
                </button>
              </div>

              <button type="button" className="auth-close-btn" onClick={() => setShowAuth(false)}>
                Close
              </button>

              {message && <p className="auth-message">{message}</p>}
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default App