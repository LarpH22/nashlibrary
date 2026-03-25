import { useState } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [isLogin, setIsLogin] = useState(true)
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: ''
  })
  const [message, setMessage] = useState('')

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const validateFrontEnd = () => {
    const trimmedUsername = formData.username.trim()
    const trimmedEmail = formData.email.trim()

    if (!trimmedUsername || !formData.password) {
      return 'Username/email and password are required.'
    }

    if (trimmedUsername.length < 3) {
      return 'Username must be at least 3 characters long.'
    }

    if (!isLogin) {
      if (!trimmedEmail) {
        return 'Email is required for registration.'
      }
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(trimmedEmail)) {
        return 'Please enter a valid email address.'
      }
    }

    if (formData.password.length < 6) {
      return 'Password must be at least 6 characters long.'
    }

    return null
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    const clientError = validateFrontEnd()
    if (clientError) {
      setMessage(clientError)
      return
    }

    try {
      const url = isLogin ? 'http://localhost:5000/login' : 'http://localhost:5000/register'
      const payload = isLogin ? { username: formData.username.trim(), password: formData.password } : {
        username: formData.username.trim(),
        email: formData.email.trim(),
        password: formData.password
      }
      const response = await axios.post(url, payload)
      setMessage(response.data.message || 'Success')
      if (isLogin && response.data.access_token) {
        localStorage.setItem('token', response.data.access_token)
        setMessage('Logged in successfully')
      }
    } catch (error) {
      setMessage(error.response?.data?.message || 'Error occurred')
    }
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Library Management System</h1>
        <p>Your gateway to knowledge</p>
      </header>
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <h2>{isLogin ? 'Welcome Back' : 'Join Our Library'}</h2>
            <p>{isLogin ? 'Sign in to access your dashboard' : 'Create an account to get started'}</p>
          </div>
          <form onSubmit={handleSubmit} className="auth-form">
            <div className="form-group">
              <label htmlFor="username">Username</label>
              <input
                type="text"
                id="username"
                name="username"
                placeholder="Enter your username"
                value={formData.username}
                onChange={handleChange}
                required
              />
            </div>
            {!isLogin && (
              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                />
              </div>
            )}
            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                name="password"
                placeholder="Enter your password"
                value={formData.password}
                onChange={handleChange}
                required
              />
            </div>
            <button type="submit" className="auth-button">
              {isLogin ? 'Sign In' : 'Create Account'}
            </button>
          </form>
          {message && <div className="message">{message}</div>}
          <div className="auth-switch">
            <p>
              {isLogin ? "Don't have an account?" : 'Already have an account?'}
              <button
                type="button"
                className="switch-button"
                onClick={() => setIsLogin(!isLogin)}
              >
                {isLogin ? 'Register here' : 'Sign in here'}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App