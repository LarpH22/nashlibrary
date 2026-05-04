import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AdminDashboard } from './AdminDashboard.jsx'
import { LibrarianDashboard } from '../librarian/LibrarianDashboard.jsx'
import { StudentDashboard } from '../student/StudentDashboard.jsx'
import { AUTH_SESSION_CLEARED_EVENT, clearStoredAuth, decodeJwtPayload, getStoredAuthToken, getStoredUserRole, isJwtExpired } from '../../shared/authStorage.js'

export function Dashboard() {
  const navigate = useNavigate()
  const token = getStoredAuthToken()
  const role = getStoredUserRole()

  useEffect(() => {
    const validRoles = ['admin', 'librarian', 'student']
    if (!token || isJwtExpired(token) || !validRoles.includes(role)) {
      clearStoredAuth()
      navigate('/login', { replace: true })
    }
  }, [navigate, role, token])

  useEffect(() => {
    const redirectToLogin = () => navigate('/login', { replace: true })
    const handleStorage = (event) => {
      if (event.key === 'access_token' || event.key === 'token' || event.key === 'user_role') {
        const nextToken = getStoredAuthToken()
        const nextRole = getStoredUserRole()
        if (!nextToken || isJwtExpired(nextToken) || !['admin', 'librarian', 'student'].includes(nextRole)) {
          redirectToLogin()
        }
      }
    }

    window.addEventListener(AUTH_SESSION_CLEARED_EVENT, redirectToLogin)
    window.addEventListener('storage', handleStorage)

    return () => {
      window.removeEventListener(AUTH_SESSION_CLEARED_EVENT, redirectToLogin)
      window.removeEventListener('storage', handleStorage)
    }
  }, [navigate])

  useEffect(() => {
    const exp = decodeJwtPayload(token)?.exp
    if (!exp) {
      return undefined
    }

    const millisecondsUntilExpiry = Math.max((Number(exp) * 1000) - Date.now(), 0)
    const timeoutId = window.setTimeout(() => {
      clearStoredAuth()
      navigate('/login', { replace: true })
    }, millisecondsUntilExpiry)

    return () => window.clearTimeout(timeoutId)
  }, [navigate, token])

  if (!token || isJwtExpired(token) || !['admin', 'librarian', 'student'].includes(role)) {
    return null
  }

  switch (role) {
    case 'admin':
      return <AdminDashboard />
    case 'librarian':
      return <LibrarianDashboard />
    case 'student':
      return <StudentDashboard />
    default:
      return null
  }
}
