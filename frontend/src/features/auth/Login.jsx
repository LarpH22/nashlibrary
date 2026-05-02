import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { loginUser, forgotPassword } from './authService.js'

export function Login({ onLoginSuccess }) {
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showForgotPassword, setShowForgotPassword] = useState(false)
  const [forgotEmail, setForgotEmail] = useState('')
  const [forgotMessage, setForgotMessage] = useState('')
  const [isForgotLoading, setIsForgotLoading] = useState(false)

  const handleChange = (event) => {
    setForm({ ...form, [event.target.name]: event.target.value })
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setIsLoading(true)
    try {
      const data = await loginUser({
        email: form.email,
        password: form.password
      })
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('user_role', data.role)
      localStorage.setItem('user_email', data.email)
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
      <section className="auth-card">
        <h2>Login</h2>
        <p className="auth-card-subtitle">Access your LIBRX account to manage books, loans, and members.</p>
        <form onSubmit={handleSubmit}>
          <label>
            Email
            <input 
              type="email" 
              name="email" 
              value={form.email} 
              onChange={handleChange}
              required 
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
          />
        </label>
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Logging in...' : 'Submit'}
        </button>
        </form>
        <div className="auth-card-footer">
          <button type="button" className="auth-link" onClick={() => navigate('/')}>Back</button>
          <span>New to LIBRX?</span>
          <button type="button" className="auth-link" onClick={() => navigate('/register')}>Create an account</button>
        </div>
        <div className="auth-card-footer">
          <button 
            type="button" 
            className="auth-link forgot-password-link" 
            onClick={() => setShowForgotPassword(true)}
          >
            Forgot Password?
          </button>
        </div>
        <p>{message}</p>
      </section>

      {showForgotPassword && (
        <div className="auth-modal-overlay" onClick={() => setShowForgotPassword(false)}>
          <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Forgot Password</h3>
            <p>Enter your email address and we will send you a link to reset your password.</p>
            <form onSubmit={handleForgotPassword}>
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
              <button type="submit" disabled={isForgotLoading}>
                {isForgotLoading ? 'Sending...' : 'Send Reset Link'}
              </button>
            </form>
            <p>{forgotMessage}</p>
            <button 
              type="button" 
              className="auth-link" 
              onClick={() => setShowForgotPassword(false)}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
