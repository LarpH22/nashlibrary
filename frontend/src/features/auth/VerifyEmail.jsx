import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import api from '../../shared/api.js'

export function VerifyEmail() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSuccess, setIsSuccess] = useState(false)
  const [canResend, setCanResend] = useState(false)
  const [showResendForm, setShowResendForm] = useState(false)
  const [resendEmail, setResendEmail] = useState('')
  const [resendLoading, setResendLoading] = useState(false)
  const [resendMessage, setResendMessage] = useState('')
  const verificationAttemptedRef = useRef(false)

  useEffect(() => {
    if (verificationAttemptedRef.current) {
      return
    }
    verificationAttemptedRef.current = true

    const verifyEmail = async () => {
      const token = searchParams.get('token')

      if (!token) {
        setMessage('Invalid verification link. No token was provided.')
        setCanResend(true)
        setIsLoading(false)
        return
      }

      try {
        const response = await api.get('/api/auth/verify-email', {
          params: { token }
        })
        setMessage(response.data?.message || 'Your email has been verified. Please wait for admin approval.')
        setIsSuccess(true)
        setCanResend(false)
      } catch (error) {
        const errorMsg = error.response?.data?.message || 'Email verification failed. Please request a new verification email.'
        setMessage(errorMsg)
        setIsSuccess(false)
        setCanResend(true)
      } finally {
        setIsLoading(false)
      }
    }

    verifyEmail()
  }, [searchParams])

  const handleResendVerification = async (event) => {
    event.preventDefault()
    setResendLoading(true)
    setResendMessage('')

    try {
      const response = await api.post('/api/auth/resend-verification', {
        email: resendEmail.trim()
      })
      setResendMessage(response.data?.message || 'Verification email sent. Please check your inbox.')
      setShowResendForm(false)
      setResendEmail('')
    } catch (error) {
      setResendMessage(error.response?.data?.message || 'Failed to resend verification email.')
    } finally {
      setResendLoading(false)
    }
  }

  const handleContinue = () => {
    navigate('/login', { replace: true })
  }

  const handleRegisterAgain = () => {
    navigate('/register', { replace: true })
  }

  if (isLoading) {
    return (
      <div className="auth-page">
        <section className="auth-card verify-card">
          <div className="verify-header">
            <div className="verify-icon">MAIL</div>
            <h2>Email Verification</h2>
          </div>
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Verifying your email address...</p>
            <p className="loading-subtitle">This works on desktop and mobile browsers.</p>
          </div>
        </section>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <section className="auth-card verify-card">
        <div className="verify-header">
          <div className="verify-icon">{isSuccess ? 'OK' : '!'}</div>
          <h2>{isSuccess ? 'Email Verified' : 'Verification Link Problem'}</h2>
        </div>

        <div className={`message ${isSuccess ? 'success' : 'error'}`}>
          <p>{message}</p>
        </div>

        {isSuccess && (
          <div className="verification-info">
            <h3>Your email has been verified.</h3>
            <ul>
              <li>Your registration is now waiting for admin approval.</li>
              <li>You will be able to log in once an admin approves your account.</li>
              <li>Please keep an eye on your email for the approval update.</li>
            </ul>
            <p className="redirect-notice">Please wait for admin approval before logging in.</p>
          </div>
        )}

        {!isSuccess && canResend && (
          <div className="resend-section">
            {!showResendForm ? (
              <>
                <p>Need a fresh verification link?</p>
                <div className="resend-actions">
                  <button onClick={() => setShowResendForm(true)} className="btn-secondary">
                    Resend Verification Email
                  </button>
                  <button onClick={handleRegisterAgain} className="btn-link">
                    Register again
                  </button>
                </div>
              </>
            ) : (
              <form onSubmit={handleResendVerification} className="resend-form">
                <p>Enter the email address you used during registration.</p>
                <input
                  type="email"
                  value={resendEmail}
                  onChange={(event) => setResendEmail(event.target.value)}
                  placeholder="student@example.com"
                  required
                  className="auth-input"
                />
                <div className="form-actions">
                  <button type="submit" className="btn-primary" disabled={resendLoading}>
                    {resendLoading ? 'Sending...' : 'Send Verification Email'}
                  </button>
                  <button type="button" onClick={() => setShowResendForm(false)} className="btn-link">
                    Cancel
                  </button>
                </div>
              </form>
            )}
            {resendMessage && (
              <p className={`resend-message ${resendMessage.toLowerCase().includes('sent') || resendMessage.toLowerCase().includes('success') ? 'success' : 'error'}`}>
                {resendMessage}
              </p>
            )}
          </div>
        )}

        <div className="action-buttons">
          <button onClick={handleContinue} className="btn-primary">
            Continue to Login
          </button>
        </div>
      </section>
    </div>
  )
}