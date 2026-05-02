import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import api from '../../shared/api.js'

export function VerifyEmail() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSuccess, setIsSuccess] = useState(false)

  useEffect(() => {
    const verifyEmail = async () => {
      const token = searchParams.get('token')
      if (!token) {
        setMessage('Invalid verification link. No token provided.')
        setIsLoading(false)
        return
      }

      try {
        const response = await api.get(`/api/auth/verify-email?token=${token}`)
        setMessage(response.data.message)
        setIsSuccess(true)
      } catch (error) {
        const errorMsg = error.response?.data?.message || 'Email verification failed'
        setMessage(`Error: ${errorMsg}`)
        setIsSuccess(false)
      } finally {
        setIsLoading(false)
      }
    }

    verifyEmail()
  }, [searchParams])

  const handleContinue = () => {
    navigate('/login')
  }

  if (isLoading) {
    return (
      <div className="auth-page">
        <section className="auth-card">
          <h2>Email Verification</h2>
          <div className="loading-spinner">
            <p>Verifying your email...</p>
          </div>
        </section>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <section className="auth-card">
        <h2>Email Verification</h2>
        <div className={`message ${isSuccess ? 'success' : 'error'}`}>
          <p>{message}</p>
        </div>
        {isSuccess && (
          <div className="verification-info">
            <p><strong>What happens next?</strong></p>
            <ul>
              <li>✅ Your email has been verified</li>
              <li>⏳ Your account is now pending admin approval</li>
              <li>📧 You will be notified once approved</li>
              <li>🔐 Only approved accounts can log in</li>
            </ul>
          </div>
        )}
        <button onClick={handleContinue} className="btn-primary">
          Continue to Login
        </button>
      </section>
    </div>
  )
}