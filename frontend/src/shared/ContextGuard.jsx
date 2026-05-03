import { useEffect, useState } from 'react'

/**
 * ContextGuard - Ensures the app is running in a valid browser context
 * Prevents chrome-error:// and other invalid contexts from running the app
 */
export function ContextGuard({ children }) {
  const [contextValid, setContextValid] = useState(true)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const validateContext = () => {
      try {
        // Check if we're in a valid browser context
        if (typeof window === 'undefined') {
          console.error('ContextGuard: No window object available')
          return false
        }

        // Prevent execution in chrome-error:// or invalid contexts
        const origin = window.location.origin
        if (!origin || origin === 'null' || origin.includes('chrome-error')) {
          console.error('ContextGuard: Invalid browser context detected:', origin)
          return false
        }

        // Ensure we have a valid protocol
        if (!window.location.protocol.match(/^https?:/)) {
          console.error('ContextGuard: Invalid protocol:', window.location.protocol)
          return false
        }

        return true
      } catch (error) {
        console.error('ContextGuard validation error:', error)
        return false
      }
    }

    // Validate immediately
    const isValid = validateContext()
    setContextValid(isValid)
    setLoading(false)

    if (!isValid) {
      // Force a page reload to try to get back into valid context
      console.warn('ContextGuard: Invalid context detected, attempting recovery...')
      setTimeout(() => {
        try {
          window.location.href = window.location.protocol + '//' + window.location.host + '/'
        } catch (e) {
          console.error('ContextGuard: Cannot recover from invalid context')
        }
      }, 1000)
    }
  }, [])

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: '#0f172a'
      }}>
        <div style={{ color: '#cbd5e1' }}>Loading...</div>
      </div>
    )
  }

  if (!contextValid) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: '#0f172a',
        color: '#cbd5e1',
        textAlign: 'center',
        padding: '20px'
      }}>
        <div>
          <h2 style={{ color: '#f87171', marginBottom: '16px' }}>Browser Context Error</h2>
          <p>This application cannot run in the current browser context.</p>
          <p style={{ fontSize: '14px', color: '#94a3b8', marginTop: '16px' }}>
            The page will automatically reload to recover...
          </p>
        </div>
      </div>
    )
  }

  return children
}
