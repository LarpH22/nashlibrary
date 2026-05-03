import { useState, useEffect, useRef } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
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
  const [contextValid, setContextValid] = useState(true)
  const verificationAttemptedRef = useRef(false)

  // Validate browser context and prevent unsafe frame execution
  useEffect(() => {
    const validateContext = () => {
      try {
        // Check if we're in a valid browser context
        if (typeof window === 'undefined') {
          console.error('No window object available')
          return false
        }

        // Prevent execution in chrome-error:// or invalid contexts
        const origin = window.location.origin
        if (!origin || origin === 'null' || origin.includes('chrome-error')) {
          console.error('Invalid browser context detected:', origin)
          return false
        }

        // Check if we're in the correct localhost context
        const isLocalhost = origin.includes('localhost') || origin.includes('127.0.0.1')
        const isProduction = process.env.NODE_ENV === 'production'

        if (!isLocalhost && !isProduction) {
          console.warn('Browser context validation: development mode with non-localhost origin')
          return true // Allow but log
        }

        return true
      } catch (error) {
        console.error('Context validation error:', error)
        return false
      }
    }

    if (!validateContext()) {
      setContextValid(false)
      setIsLoading(false)
      setMessage('Browser context error. Please refresh the page or click the verification link again.')
      return
    }

    setContextValid(true)
  }, [])

  // Perform email verification only after context is valid
  useEffect(() => {
    if (!contextValid || verificationAttemptedRef.current) {
      return
    }

    // Mark that we're attempting verification
    verificationAttemptedRef.current = true

    const verifyEmail = async () => {
      try {
        // Ensure DOM is ready
        await new Promise(resolve => {
          if (document.readyState === 'complete') {
            resolve()
          } else {
            window.addEventListener('load', resolve, { once: true })
          }
        })

        const token = searchParams.get('token')

        if (!token) {
          setMessage('Invalid verification link. No token provided.')
          setCanResend(true)
          setIsLoading(false)
          return
        }

        // Perform API verification
        try {
          const response = await api.get(`/api/auth/verify-email?token=${encodeURIComponent(token)}`)
          setMessage(response.data.message || 'Email verified successfully!')
          setIsSuccess(true)

          // Use safe router navigation instead of window.location
          setTimeout(() => {
            navigate('/login', { replace: true })
          }, 3000)
        } catch (error) {
          const errorMsg = error.response?.data?.message || error.message || 'Email verification failed'
          setMessage(errorMsg)
          setIsSuccess(false)
          setCanResend(true)
        }
      } catch (error) {
        console.error('Verification process error:', error)
        setMessage('An unexpected error occurred. Please try again.')
        setCanResend(true)
      } finally {
        setIsLoading(false)
      }
    }

    verifyEmail()
  }, [searchParams, navigate, contextValid])

  const handleResendVerification = async (e) => {
    e.preventDefault()

    if (!contextValid) {
      setResendMessage('Cannot resend in current browser context. Please refresh the page.')
      return
    }

    setResendLoading(true)
    setResendMessage('')

    try {
      const response = await api.post('/api/auth/resend-verification', {
        email: resendEmail
      })
      setResendMessage(response.data.message)
      setShowResendForm(false)
      setResendEmail('')
    } catch (error) {
      const errorMsg = error.response?.data?.message || error.message || 'Failed to resend verification email'
      setResendMessage(errorMsg)
    } finally {
      setResendLoading(false)
    }
  }

  const handleContinue = () => {
    if (!contextValid) {
      setMessage('Cannot navigate in current context. Please refresh the page.')
      return
    }
    navigate('/login', { replace: true })
  }

  const handleRegisterAgain = () => {
    if (!contextValid) {
      setMessage('Cannot navigate in current context. Please refresh the page.')
      return
    }
    navigate('/register', { replace: true })
  }

  // Show context error state
  if (!contextValid) {
    return (
      <div className="auth-page">
        <section className="auth-card verify-card">
          <div className="verify-header">
            <div className="verify-icon">⚠️</div>
            <h2>Browser Context Error</h2>
          </div>
          <div className="message error">
            <p>Unable to verify email in the current browser context.</p>
          </div>
          <div className="context-error-info">
            <p>This page encountered a browser security issue. Here's what to do:</p>
            <ul>
              <li>🔄 <strong>Refresh this page</strong> to reload in the correct context</li>
              <li>📧 Or <strong>click the verification link again</strong> from your email</li>
              <li>💻 Make sure you're using a standard web browser (Chrome, Firefox, Safari, Edge)</li>
            </ul>
          </div>
          <div className="action-buttons">
            <button
              onClick={() => window.location.reload()}
              className="btn-primary"
            >
              Refresh Page
            </button>
          </div>
        </section>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="auth-page">
        <section className="auth-card verify-card">
          <div className="verify-header">
            <div className="verify-icon">📧</div>
            <h2>Email Verification</h2>
          </div>

          <div className="loading-state">
            <div className="spinner"></div>
            <p>Verifying your email address...</p>
            <p className="loading-subtitle">This may take a few seconds</p>
          </div>
        </section>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <section className="auth-card verify-card">
        <div className="verify-header">
          <div className="verify-icon">{isSuccess ? '✅' : '❌'}</div>
          <h2>Email Verification</h2>
        </div>

        <div className={`message ${isSuccess ? 'success' : 'error'}`}>
          <p>{message}</p>
        </div>

        {isSuccess && (
          <div className="verification-info">
            <h3>What happens next?</h3>
            <ul>
              <li>✅ Your email has been verified</li>
              <li>⏳ Your account is now pending admin approval</li>
              <li>📧 You will be notified once approved</li>
              <li>🔐 Only approved accounts can log in</li>
            </ul>
            <p className="redirect-notice">Redirecting to login page in a few seconds...</p>
          </div>
        )}

        {!isSuccess && canResend && (
          <div className="resend-section">
            {!showResendForm ? (
              <>
                <p>Need a new verification email?</p>
                <div className="resend-actions">
                  <button
                    onClick={() => setShowResendForm(true)}
                    className="btn-secondary"
                  >
                    Resend Verification Email
                  </button>
                  <button
                    onClick={handleRegisterAgain}
                    className="btn-link"
                  >
                    Or register again
                  </button>
                </div>
              </>
            ) : (
              <form onSubmit={handleResendVerification} className="resend-form">
                <p>Enter your email address to receive a new verification link:</p>
                <input
                  type="email"
                  value={resendEmail}
                  onChange={(e) => setResendEmail(e.target.value)}
                  placeholder="Enter your email"
                  required
                  className="auth-input"
                />
                <div className="form-actions">
                  <button
                    type="submit"
                    className="btn-primary"
                    disabled={resendLoading}
                  >
                    {resendLoading ? 'Sending...' : 'Send Verification Email'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowResendForm(false)}
                    className="btn-link"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}
            {resendMessage && (
              <p className={`resend-message ${resendMessage.includes('successfully') ? 'success' : 'error'}`}>
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