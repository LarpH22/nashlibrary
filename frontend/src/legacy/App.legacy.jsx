import './App.css'
import { useState, useEffect } from 'react'
import axios from 'axios'
import { Search, Users, ClipboardList, Bell } from 'lucide-react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (window.location.port && window.location.port !== '5000' ? 'http://localhost:5000' : '')
if (API_BASE_URL) {
  axios.defaults.baseURL = API_BASE_URL
}

import StudentInterface from './components/StudentInterface'
import LibrarianDashboard from './components/LibrarianDashboard'
import AdminDashboard from './components/AdminDashboard'

function App() {
  const [showAuth, setShowAuth] = useState(false)
  const [isLogin, setIsLogin] = useState(true)
  const [isForgotPassword, setIsForgotPassword] = useState(false)
  const [isResetPassword, setIsResetPassword] = useState(false)
  const [resetToken, setResetToken] = useState('')

  const [formData, setFormData] = useState({
    username: '',
    full_name: '',
    email: '',
    password: '',
    student_id: '',
    registration_document: null,
    new_password: '',
    confirm_password: ''
  })

  const [authMessage, setAuthMessage] = useState('')
  const [registrationSuccessOpen, setRegistrationSuccessOpen] = useState(false)
  const [registrationSuccessMessage, setRegistrationSuccessMessage] = useState('')
  const [isAuthLoading, setIsAuthLoading] = useState(false)
  const [isCheckingAuth, setIsCheckingAuth] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
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
    const token = new URLSearchParams(window.location.search).get('token')
    if (token) {
      setResetToken(token)
      setIsResetPassword(true)
      setShowAuth(true)
      setIsLogin(false)
      setIsForgotPassword(false)
    }
  }, [])

  useEffect(() => {
    const token =
      localStorage.getItem('token') ||
      localStorage.getItem('access_token')

    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      fetchUser().then(() => setIsCheckingAuth(false))
    } else {
      setIsCheckingAuth(false)
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
      localStorage.removeItem('activeTab')
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
    const { name, type, files, value } = e.target
    if (type === 'file') {
      setFormData((prev) => ({
        ...prev,
        [name]: files[0] || null
      }))
    } else {
      setFormData((prev) => ({
        ...prev,
        [name]: value
      }))
    }
  }

  const resetForm = () => {
    setFormData({
      username: '',
      full_name: '',
      email: '',
      password: '',
      student_id: '',
      registration_document: null,
      new_password: '',
      confirm_password: ''
    })
  }

  const openLoginModal = () => {
    setShowAuth(true)
    setIsLogin(true)
    setIsForgotPassword(false)
    setIsResetPassword(false)
    setAuthMessage('')
    setResetToken('')
    resetForm()
  }

  const openRegisterModal = () => {
    setShowAuth(true)
    setIsLogin(false)
    setIsForgotPassword(false)
    setIsResetPassword(false)
    setAuthMessage('')
    resetForm()
  }

  const openForgotPasswordModal = () => {
    setShowAuth(true)
    setIsLogin(false)
    setIsForgotPassword(true)
    setIsResetPassword(false)
    setAuthMessage('')
    resetForm()
  }

  const closeAuthModal = () => {
    setShowAuth(false)
    setIsForgotPassword(false)
    setIsResetPassword(false)
    setIsLogin(true)
    setAuthMessage('')
    setResetToken('')
    resetForm()
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    console.log('handleSubmit fired', { isLogin, isForgotPassword, isResetPassword, formData })
    setAuthMessage('')
    setIsAuthLoading(true)

    try {
      if (isResetPassword) {
        if (formData.new_password !== formData.confirm_password) {
          setAuthMessage('Passwords do not match')
          return
        }
        const res = await axios.post('/reset-password', {
          token: resetToken,
          new_password: formData.new_password
        })
        setAuthMessage(res.data.message)
        setIsResetPassword(false)
        setResetToken('')
        resetForm()
        // Clear URL parameters
        window.history.replaceState({}, document.title, window.location.pathname)
      } else if (isForgotPassword) {
        const res = await axios.post('/forgot-password', {
          email: formData.email
        })
        setAuthMessage(res.data.message)
        setIsForgotPassword(false)
        resetForm()
      } else if (isLogin) {
        const res = await axios.post('/api/auth/login', {
          password: formData.password
        })

        const token = res.data.access_token

        localStorage.setItem('token', token)
        localStorage.setItem('access_token', token)
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`

        setUserRole(res.data.role)
        setIsAuthenticated(true)

        await fetchUser()

        setShowAuth(false)
        resetForm()
      } else {
        const email = formData.email.trim().toLowerCase()
        const fullName = formData.full_name.trim()

        if (!fullName || !email || !formData.password) {
          setAuthMessage('Please fill in your full name, email, and password.')
          return
        }

        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        if (!emailPattern.test(email)) {
          setAuthMessage('Please enter a valid email address.')
          return
        }

        if (!email.endsWith('@gmail.com') && !email.endsWith('.edu.ph')) {
          setAuthMessage('Email must end with @gmail.com or .edu.ph')
          return
        }

        // Validate password strength
        const strongPassword = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/
        if (!strongPassword.test(formData.password)) {
          setAuthMessage('Password must be at least 8 characters and include uppercase, lowercase, number, and special character.')
          return
        }

        // Validate file upload size
        if (formData.registration_document && formData.registration_document.size > 5 * 1024 * 1024) {
          setAuthMessage('Registration document must be 5MB or smaller.')
          return
        }

        // Validate that file is uploaded
        if (!formData.registration_document) {
          setAuthMessage('School Registration Document is required. Please upload a PDF, JPG, JPEG, or PNG file.')
          return
        }

        // Validate file type
        const allowedExtensions = ['pdf', 'jpg', 'jpeg', 'png']
        const fileName = formData.registration_document.name.toLowerCase()
        const fileExtension = fileName.split('.').pop()
        if (!allowedExtensions.includes(fileExtension)) {
          setAuthMessage('Invalid file type. Only PDF, JPG, JPEG, and PNG files are allowed.')
          return
        }

        // Create FormData to handle file upload
        const formDataToSend = new FormData()
        formDataToSend.append('full_name', formData.full_name.trim())
        formDataToSend.append('email', formData.email.trim())
        formDataToSend.append('password', formData.password)
        // Only append student_id if provided
        if (formData.student_id && formData.student_id.trim()) {
          formDataToSend.append('student_id', formData.student_id.trim())
        }
        formDataToSend.append('registration_document', formData.registration_document)

        // Log FormData contents for debugging
        console.log('Form submission - Contents:', {
          full_name: formData.full_name,
          email: formData.email,
          password: '***',
          student_id: formData.student_id,
          has_file: !!formData.registration_document,
          file_name: formData.registration_document?.name || 'none'
        })

        const res = await axios.post('/api/auth/register', formDataToSend)

        const successMessage = res.data.message || 'Registration submitted. Please verify your email and wait for admin or librarian approval before logging in.'
        if (res.status === 201 || res.status === 200) {
          setRegistrationSuccessMessage(successMessage)
          setRegistrationSuccessOpen(true)
          setShowAuth(false)
          resetForm()
        } else {
          setAuthMessage(successMessage)
        }
      }
    } catch (err) {
      console.error('Registration request failed:', err)
      const responseData = err.response?.data
      const serverMessage = responseData?.message || (responseData ? JSON.stringify(responseData) : null)
      setAuthMessage(serverMessage || err.response?.statusText || err.message || 'Something went wrong')
    } finally {
      setIsAuthLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('access_token')
    localStorage.removeItem('studentActiveTab')
    localStorage.removeItem('librarianActivePanel')
    localStorage.removeItem('adminActivePanel')
    delete axios.defaults.headers.common['Authorization']

    setIsAuthenticated(false)
    setUserRole('')
    setUser(null)
  }

  // Show loading state while checking authentication
  if (isCheckingAuth) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: '#0a0f1e',
        color: '#fff',
        fontFamily: 'Arial, sans-serif'
      }}>
        <div style={{ textAlign: 'center' }}>
          <h2>Loading...</h2>
          <p>Restoring your session...</p>
        </div>
      </div>
    )
  }

  if (isAuthenticated) {
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
            <span className="brand-name">LIBRASYS</span>
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
            <button type="button" className="secondary-btn" onClick={handleLogout}>
              Logout
            </button>
          ) : (
            <>
              <button type="button" className="secondary-btn" onClick={openLoginModal}>
                Login
              </button>
              <button type="button" className="primary-btn" onClick={openRegisterModal}>
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
                <button type="button" className="primary-btn" onClick={openRegisterModal}>Get Started</button>
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
          © {new Date().getFullYear()} LIBRASYS
        </footer>
      </main>

      {showAuth && (
        <div className="auth-modal">
          <div className="auth-form">
            <h3>{isResetPassword ? 'Reset Password' : isForgotPassword ? 'Forgot Password' : isLogin ? 'Login' : 'Register'}</h3>

            <form onSubmit={handleSubmit}>
              {isResetPassword ? (
                <>
                  <label>
                    New Password
                    <input
                      name="new_password"
                      type="password"
                      autoComplete="new-password"
                      placeholder="Enter new password (8+ chars, uppercase, lowercase, number)"
                      onChange={handleInputChange}
                      required
                    />
                  </label>

                  <label>
                    Confirm New Password
                    <input
                      name="confirm_password"
                      type="password"
                      autoComplete="new-password"
                      placeholder="Confirm new password"
                      onChange={handleInputChange}
                      required
                    />
                  </label>
                  <p className="forgot-password-info">
                    Enter your new password. Make sure it meets the requirements.
                  </p>
                </>
              ) : isForgotPassword ? (
                <>
                  <label>
                    Email
                    <input
                      name="email"
                      type="email"
                      autoComplete="email"
                      placeholder="Enter your email"
                      onChange={handleInputChange}
                      required
                    />
                  </label>
                  <p className="forgot-password-info">
                    Enter your email address and we will send you a link to reset your password.
                  </p>
                </>
              ) : isLogin ? (
                <>
                  <label>
                    Email or Username
                    <input
                      name="username"
                      autoComplete="username"
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
                      autoComplete="current-password"
                      placeholder="Enter your password"
                      onChange={handleInputChange}
                      required
                    />
                  </label>
                  <button type="button" className="forgot-password-link" onClick={openForgotPasswordModal}>
                    Forgot Password?
                  </button>
                </>
              ) : (
                <>
                  <label>
                    Full Name
                    <input
                      name="full_name"
                      autoComplete="name"
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
                      autoComplete="email"
                      placeholder="Enter your email (@gmail.com or .edu.ph)"
                      onChange={handleInputChange}
                      required
                    />
                  </label>

                  <label>
                    Student ID (Optional)
                    <input
                      name="student_id"
                      placeholder="Enter your student ID"
                      onChange={handleInputChange}
                    />
                  </label>

                  <label>
                    Password
                    <input
                      name="password"
                      type="password"
                      autoComplete="new-password"
                      placeholder="Strong password (8+ chars, uppercase, lowercase, number)"
                      onChange={handleInputChange}
                      required
                    />
                  </label>

                  <label>
                    School Registration Document (Required - PDF/JPG/JPEG/PNG, Max 5MB)
                    <input
                      name="registration_document"
                      type="file"
                      accept=".pdf,.jpg,.jpeg,.png"
                      onChange={handleInputChange}
                      required
                    />
                  </label>

                </>
              )}

              <div className="auth-actions-row">
                <button type="submit" className="primary-btn" disabled={isAuthLoading}>
                  {isAuthLoading
                    ? isResetPassword
                      ? 'Resetting...'
                      : isForgotPassword
                      ? 'Sending...'
                      : isLogin
                      ? 'Logging in...'
                      : 'Registering...'
                    : isResetPassword
                    ? 'Reset Password'
                    : isForgotPassword
                    ? 'Send Reset Link'
                    : isLogin
                    ? 'Login'
                    : 'Register'}
                </button>
                {!isResetPassword && !isForgotPassword && (
                  <button type="button" className="secondary-btn" onClick={isLogin ? openRegisterModal : openLoginModal}>
                    {isLogin ? 'Switch to Register' : 'Switch to Login'}
                  </button>
                )}
                {isForgotPassword && (
                  <button type="button" className="secondary-btn" onClick={() => setIsForgotPassword(false)}>
                    Back to Login
                  </button>
                )}
                {isResetPassword && (
                  <button type="button" className="secondary-btn" onClick={() => { setIsResetPassword(false); setResetToken(''); setShowAuth(false); window.history.replaceState({}, document.title, window.location.pathname) }}>
                    Cancel
                  </button>
                )}
              </div>

              <button type="button" className="auth-close-btn" onClick={closeAuthModal}>
                Close
              </button>

              {authMessage && <p className="auth-message">{authMessage}</p>}
            </form>
          </div>
        </div>
      )}

      {registrationSuccessOpen && (
        <div className="auth-modal">
          <div className="auth-form">
            <h3>Registration Submitted</h3>
            <p>{registrationSuccessMessage}</p>
            <button type="button" className="primary-btn" onClick={() => setRegistrationSuccessOpen(false)}>
              Okay
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default App