import './App.css'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LibrxLanding from './LibrxLanding.jsx'
import { Login } from '../features/auth/Login.jsx'
import { Register } from '../features/auth/Register.jsx'
import { Dashboard } from '../features/dashboard/Dashboard.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LibrxLanding />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  )
}
