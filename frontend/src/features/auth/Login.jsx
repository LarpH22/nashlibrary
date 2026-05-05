import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { loginUser, forgotPassword } from './authService.js'
import { clearStoredAuth, getStoredAuthToken, getStoredUserRole, isJwtExpired, saveLoginSession } from '../../shared/authStorage.js'

export function Login({ onLoginSuccess }) {
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showForgotPassword, setShowForgotPassword] = useState(false)
  const [forgotEmail, setForgotEmail] = useState('')
  const [forgotMessage, setForgotMessage] = useState('')
  const [isForgotLoading, setIsForgotLoading] = useState(false)

  useEffect(() => {
    const token = getStoredAuthToken()
    const role = getStoredUserRole()
    if (token && !isJwtExpired(token) && ['admin', 'librarian', 'student'].includes(role)) {
      navigate('/dashboard', { replace: true })
    }
  }, [navigate])

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setIsLoading(true)
    try {
      clearStoredAuth()
      const data = await loginUser({
        email: form.email,
        password: form.password
      })
      saveLoginSession(data)
      if (onLoginSuccess) {
        onLoginSuccess()
      }
      navigate('/dashboard')
      console.log('Login successful:', data)
    } catch (error) {
      const errorMsg = error.response?.data?.message || error.message || 'Login failed'
      console.error('Login error:', errorMsg, error)
      setMessage(`Error: ${errorMsg}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleForgotPassword = async (event) => {
    event.preventDefault()
    setIsForgotLoading(true)
    setForgotMessage('')
    try {
      await forgotPassword({ email: forgotEmail })
      setForgotMessage('Password reset link sent to your email')
      setTimeout(() => {
        setShowForgotPassword(false)
        setForgotEmail('')
        setForgotMessage('')
      }, 3000)
    } catch (error) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to send reset email'
      setForgotMessage(`Error: ${errorMsg}`)
    } finally {
      setIsForgotLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <section className="auth-card login-card">
        <h2>Login</h2>
        <p className="auth-card-subtitle">Access your LIBRASYS account to manage books, loans, and members.</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            Email
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              required
              placeholder="librarian1@library.com"
            />
          </label>

          <label>
            Password
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              required
              placeholder="Enter your password"
            />
          </label>

          <button type="submit" className="auth-button auth-button-primary" disabled={isLoading}>
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="auth-card-footer auth-card-actions">
          <button type="button" className="auth-button auth-button-secondary" onClick={() => navigate('/')}>Back</button>
          <span className="auth-card-note">New to LIBRASYS?</span>
          <button type="button" className="auth-button auth-button-outline" onClick={() => navigate('/register')}>Create an account</button>
        </div>

        <div className="auth-card-footer auth-card-link-row">
          <button
            type="button"
            className="auth-link forgot-password-link"
            onClick={() => setShowForgotPassword(true)}
          >
            Forgot Password?
          </button>
        </div>

        {message && <p className="auth-status">{message}</p>}
      </section>

      {showForgotPassword && (
        <div className="auth-modal-overlay" onClick={() => setShowForgotPassword(false)}>
          <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
            <div className="auth-modal-header">
              <div>
                <h3>Forgot Password</h3>
                <p className="auth-modal-description">Enter your email address and we will send you a link to reset your password.</p>
              </div>
              <button type="button" className="auth-modal-close" onClick={() => setShowForgotPassword(false)} aria-label="Close password reset modal">
                ×
              </button>
            </div>

            <form onSubmit={handleForgotPassword} className="auth-modal-form">
              <label>
                Email
                <input
                  type="email"
                  value={forgotEmail}
                  onChange={(e) => setForgotEmail(e.target.value)}
                  required
                  placeholder="Enter your email"
                />
              </label>
              <button type="submit" className="auth-button auth-button-primary" disabled={isForgotLoading}>
                {isForgotLoading ? 'Sending...' : 'Send Reset Link'}
              </button>
            </form>

            {forgotMessage && (
              <p className={`auth-modal-message ${forgotMessage.startsWith('Error') ? 'error' : 'success'}`}>
                {forgotMessage}
              </p>
            )}

            <button type="button" className="auth-link auth-modal-cancel" onClick={() => setShowForgotPassword(false)}>
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
