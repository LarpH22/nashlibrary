import './App.css'
import { useEffect, useRef } from 'react'
import { BrowserRouter, Routes, Route, useLocation, useNavigate } from 'react-router-dom'
import { ContextGuard } from '../shared/ContextGuard.jsx'
import LibrxLanding from './LibrxLanding.jsx'
import { Login } from '../features/auth/Login.jsx'
import { Register } from '../features/auth/Register.jsx'
import { VerifyEmail } from '../features/auth/VerifyEmail.jsx'
import ResetPassword from '../features/auth/ResetPassword.jsx'
import { Dashboard } from '../features/dashboard/Dashboard.jsx'
import { ResourceDetailPage } from '../features/catalog/ResourceDetailPage.jsx'
import { getStoredAuthToken, getStoredUserRole, isJwtExpired } from '../shared/authStorage.js'

function DashboardStayGuard() {
  const location = useLocation()
  const navigate = useNavigate()
  const lockedDashboardPathRef = useRef('')

  useEffect(() => {
    const token = getStoredAuthToken()
    const role = getStoredUserRole()
    const authenticatedDashboardUser = token && !isJwtExpired(token) && ['admin', 'librarian', 'student'].includes(role)
    const currentPath = `${location.pathname}${location.search}${location.hash}`

    if (authenticatedDashboardUser && location.pathname.startsWith('/dashboard')) {
      lockedDashboardPathRef.current = currentPath
      window.history.replaceState({ dashboardLocked: true }, '', currentPath)
    }

    if (authenticatedDashboardUser && lockedDashboardPathRef.current && !location.pathname.startsWith('/dashboard')) {
      navigate(lockedDashboardPathRef.current, { replace: true })
    }
  }, [location.hash, location.pathname, location.search, navigate])

  useEffect(() => {
    const keepDashboardOpen = () => {
      const lockedPath = lockedDashboardPathRef.current
      const token = getStoredAuthToken()
      const role = getStoredUserRole()
      const authenticatedDashboardUser = token && !isJwtExpired(token) && ['admin', 'librarian', 'student'].includes(role)

      if (!lockedPath || !authenticatedDashboardUser) {
        return
      }

      window.history.pushState({ dashboardLocked: true }, '', lockedPath)
      navigate(lockedPath, { replace: true })
    }

    window.addEventListener('popstate', keepDashboardOpen)
    return () => window.removeEventListener('popstate', keepDashboardOpen)
  }, [navigate])

  return null
}

export default function App() {
  return (
    <ContextGuard>
      <BrowserRouter>
        <DashboardStayGuard />
        <Routes>
          <Route path="/" element={<LibrxLanding />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/dashboard/*" element={<Dashboard />} />
          <Route path="/books/:bookId" element={<ResourceDetailPage type="book" />} />
          <Route path="/ebooks/:ebookId" element={<ResourceDetailPage type="ebook" />} />
        </Routes>
      </BrowserRouter>
    </ContextGuard>
  )
}
