import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { registerUser } from './authService.js'

export function Register() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    student_id: '',
    registration_document: null
  })
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleChange = (event) => {
    const { name, value, files } = event.target
    if (name === 'registration_document') {
      setForm({
        ...form,
        registration_document: files?.[0] || null
      })
      return
    }

    setForm({
      ...form,
      [name]: value
    })
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setIsLoading(true)
    try {
      const data = await registerUser(form)
      localStorage.setItem('access_token', data.access_token || '')
      localStorage.setItem('user_role', data.role || 'student')
      setMessage(`Registration successful! Welcome, ${data.email}`)
      console.log('Registration successful:', data)
      setForm({
        full_name: '',
        email: '',
        password: '',
        student_id: '',
        registration_document: null
      })
    } catch (error) {
      const errorMsg = error.message || 'Registration failed'
      console.error('Registration error:', errorMsg, error)
      setMessage(`Error: ${errorMsg}`)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <section className="auth-card">
        <h2>Register</h2>
        <p className="auth-card-subtitle">Create your account to start borrowing books and managing your library profile.</p>
        <form onSubmit={handleSubmit}>
          <label>
            Full Name
            <input type="text" name="full_name" value={form.full_name} onChange={handleChange} required />
          </label>
          <label>
            Email
            <input type="email" name="email" value={form.email} onChange={handleChange} required />
          </label>
          <label>
            Password
            <input type="password" name="password" value={form.password} onChange={handleChange} required />
          </label>
          <label>
            Student ID
            <input
              type="text"
              name="student_id"
              value={form.student_id}
              onChange={handleChange}
              placeholder="e.g., STU2024001"
            />
          </label>
          <label>
            Registration Document
            <input
              type="file"
              name="registration_document"
              accept=".pdf,.doc,.docx"
              onChange={handleChange}
              required
            />
            {form.registration_document && (
              <span className="file-name">Selected: {form.registration_document.name}</span>
            )}
          </label>
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Registering...' : 'Submit'}
          </button>
        </form>
      <div className="auth-card-footer">
        <span>Already have an account?</span>
        <button type="button" className="auth-link" onClick={() => navigate('/login')}>Sign in</button>
      </div>
      <p>{message}</p>
    </section>
  </div>
  )
}
