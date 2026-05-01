import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AdminDashboard } from './AdminDashboard.jsx'
import { LibrarianDashboard } from '../librarian/LibrarianDashboard.jsx'
import { StudentDashboard } from '../student/StudentDashboard.jsx'

export function Dashboard() {
  const navigate = useNavigate()
  const role = localStorage.getItem('user_role')

  useEffect(() => {
    if (!role) {
      navigate('/login', { replace: true })
    }
  }, [navigate, role])

  if (!role) {
    return null
  }

  switch (role) {
    case 'admin':
      return <AdminDashboard />
    case 'librarian':
      return <LibrarianDashboard />
    case 'student':
    default:
      return <StudentDashboard />
  }
}
