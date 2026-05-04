import './App.css'
import { useEffect, useRef } from 'react'
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { ContextGuard } from '../shared/ContextGuard.jsx'
import LibrxLanding from './LibrxLanding.jsx'
import { Login } from '../features/auth/Login.jsx'
import { Register } from '../features/auth/Register.jsx'
import { VerifyEmail } from '../features/auth/VerifyEmail.jsx'
import ResetPassword from '../features/auth/ResetPassword.jsx'
import { Dashboard } from '../features/dashboard/Dashboard.jsx'
import { clearStoredAuth, getStoredAuthToken } from '../shared/authStorage.js'

function DashboardExitGuard() {
  const location = useLocation()
  const previousPathRef = useRef(location.pathname)

  useEffect(() => {
    const previousPath = previousPathRef.current
    const currentPath = location.pathname
    const leftDashboard = previousPath.startsWith('/dashboard') && !currentPath.startsWith('/dashboard')

    if (leftDashboard && getStoredAuthToken()) {
      clearStoredAuth()
    }

    previousPathRef.current = currentPath
  }, [location.pathname])

  return null
}

export default function App() {
  return (
    <ContextGuard>
      <BrowserRouter>
        <DashboardExitGuard />
        <Routes>
          <Route path="/" element={<LibrxLanding />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/dashboard/*" element={<Dashboard />} />
        </Routes>
      </BrowserRouter>
    </ContextGuard>
  )
}
