import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { loginUser } from './authService.js'

export function Login({ onLoginSuccess }) {
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)

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
        <p>{message}</p>
      </section>
    </div>
  )
}
