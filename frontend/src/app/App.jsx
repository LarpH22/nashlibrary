import './App.css'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ContextGuard } from '../shared/ContextGuard.jsx'
import LibrxLanding from './LibrxLanding.jsx'
import { Login } from '../features/auth/Login.jsx'
import { Register } from '../features/auth/Register.jsx'
import { VerifyEmail } from '../features/auth/VerifyEmail.jsx'
import ResetPassword from '../features/auth/ResetPassword.jsx'
import { Dashboard } from '../features/dashboard/Dashboard.jsx'
import { ResourceDetailPage } from '../features/catalog/ResourceDetailPage.jsx'

export default function App() {
  return (
    <ContextGuard>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LibrxLanding />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/books/:bookId" element={<ResourceDetailPage type="book" />} />
          <Route path="/ebooks/:ebookId" element={<ResourceDetailPage type="ebook" />} />
        </Routes>
      </BrowserRouter>
    </ContextGuard>
  )
}
