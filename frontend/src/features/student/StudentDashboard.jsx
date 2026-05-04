import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  BarChart3,
  Bell,
  BookOpen,
  BookMarked,
  CheckCircle2,
  Flame,
  History,
  KeyRound,
  Library,
  LogOut,
  Search,
  User,
  X
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { BookSearch } from '../books/BookSearch.jsx'
import { fetchMostBorrowedBooks, returnBook } from '../books/bookService.js'
import { clearStoredAuth, decodeJwtPayload, getStoredAuthToken, getStoredUserRole, isJwtExpired } from '../../shared/authStorage.js'
import './StudentDashboard.css'

const navSections = [
  {
    section: 'MAIN',
    items: [
      { id: 'overview', icon: BarChart3, title: 'Overview' },
      { id: 'books', icon: BookOpen, title: 'My Borrowed Books' },
      { id: 'popular', icon: Flame, title: 'Top Books' },
      { id: 'catalog', icon: Search, title: 'Search Catalog' },
      { id: 'ebooks', icon: BookMarked, title: 'E-books' },
      { id: 'reading', icon: BookMarked, title: 'Reading History' },
      { id: 'history', icon: History, title: 'Borrowing History' }
    ]
  },
  {
    section: 'ACCOUNT',
    items: [
      { id: 'profile', icon: User, title: 'My Profile' },
      { id: 'password', icon: KeyRound, title: 'Change Password' }
    ]
  }
]

const pageTitles = {
  overview: 'Overview',
  books: 'My Borrowed Books',
  popular: 'Top Books',
  catalog: 'Search Catalog',
  ebooks: 'E-books',
  reading: 'Reading History',
  history: 'Borrowing History',
  profile: 'My Profile',
  password: 'Change Password'
}

const formatDate = (value) => {
  if (!value) {
    return ''
  }
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleString()
}

const displayValue = (value) => (value === null || value === undefined ? '' : String(value))

const isRegistrationStudentId = (value) => /^\d{3}-\d{4}$/.test(String(value || ''))

const loanStatus = (loan) => String(loan?.status || '').toLowerCase()
const isPendingRequest = (loan) => loanStatus(loan) === 'pending'
const isRejectedRequest = (loan) => loanStatus(loan) === 'rejected'
const isApprovedLoan = (loan) => !loan.is_request && ['active', 'borrowed', 'overdue'].includes(loanStatus(loan)) && !loan.returned

const getInitials = (name = '') => {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) {
    return 'S'
  }
  return parts.slice(0, 2).map((part) => part[0].toUpperCase()).join('')
}

const getStatIcon = (label) => {
  if (label === 'Borrowed') return BookOpen
  if (label === 'Overdue') return AlertTriangle
  if (label === 'Returned') return CheckCircle2
  return History
}

export function StudentDashboard() {
  const navigate = useNavigate()
  const [activePage, setActivePage] = useState('overview')
  const [loans, setLoans] = useState([])
  const [profile, setProfile] = useState(null)
  const [popularBooks, setPopularBooks] = useState([])
  const [ebooks, setEbooks] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [passwordForm, setPasswordForm] = useState({ old_password: '', new_password: '' })
  const [notifications, setNotifications] = useState([])
  const [showNotifications, setShowNotifications] = useState(false)
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)
  const [loading, setLoading] = useState(true)
  const [fetchError, setFetchError] = useState('')
  const [authStatus, setAuthStatus] = useState('pending')
  const [authMessage, setAuthMessage] = useState('')
  const [showEditProfile, setShowEditProfile] = useState(false)
  const [editProfileForm, setEditProfileForm] = useState({
    full_name: '',
    email: ''
  })
  const [editProfileErrors, setEditProfileErrors] = useState({})
  const [savingProfile, setSavingProfile] = useState(false)

  const addNotification = useCallback((text) => {
    const id = Date.now()
    setNotifications((prev) => [...prev, { id, text, timestamp: new Date() }])
  }, [])

  const getAuthToken = useCallback(() => {
    return getStoredAuthToken()
  }, [])

  const decodeTokenRole = useCallback((token) => {
    const parsed = decodeJwtPayload(token)
    return parsed?.role || parsed?.user_role || null
  }, [])

  const removeNotification = useCallback((id) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))
  }, [])

  const clearSession = useCallback(() => {
    clearStoredAuth()
  }, [])

  const redirectToLogin = useCallback(() => {
    clearSession()
    navigate('/login', { replace: true })
  }, [clearSession, navigate])

  const handleLogout = () => {
    clearSession()
    navigate('/login', { replace: true })
  }

  const loadLoans = useCallback(async () => {
    try {
      const token = getAuthToken()
      const response = await fetch('/api/loans/student', {
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        }
      })
      if (response.status === 401) {
        console.warn('[StudentDashboard] loadLoans unauthorized', response)
        redirectToLogin()
        return
      }
      const data = await response.json()
      console.log('[StudentDashboard] loadLoans response', response.status, data)
      if (!response.ok) {
        throw new Error(data?.message || 'Unable to load student loans')
      }
      setLoans(Array.isArray(data) ? data : [])
    } catch (err) {
      const message = err?.message || 'Unable to load your books.'
      console.error('[StudentDashboard] loadLoans error', err)
      setFetchError(message)
      addNotification(message)
    }
  }, [addNotification, getAuthToken, redirectToLogin])

  const loadProfile = useCallback(async () => {
    try {
      const token = getAuthToken()
      const response = await fetch('/api/students/profile', {
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        }
      })
      if (response.status === 401) {
        console.warn('[StudentDashboard] loadProfile unauthorized', response)
        redirectToLogin()
        return
      }
      const data = await response.json()
      console.log('[StudentDashboard] loadProfile response', response.status, data)
      if (!response.ok) {
        throw new Error(data?.message || 'Unable to load profile')
      }
      const role = data?.role || data?.user_role || getStoredUserRole()
      if (role && role !== 'student') {
        setAuthStatus('unauthorized')
        setAuthMessage('Unauthorized access. Login with a student account to continue.')
        console.warn('[StudentDashboard] profile role mismatch', { role, data })
        return
      }
      setProfile(data)
    } catch (err) {
      const message = err?.message || 'Unable to load profile.'
      console.error('[StudentDashboard] loadProfile error', err)
      setFetchError(message)
      addNotification(message)
    }
  }, [addNotification, getAuthToken, redirectToLogin])

  const loadPopularBooks = useCallback(async () => {
    try {
      const response = await fetchMostBorrowedBooks(5)
      setPopularBooks(Array.isArray(response?.books) ? response.books : [])
    } catch (err) {
      console.error('[StudentDashboard] loadPopularBooks error', err)
      addNotification('Unable to load the most borrowed books.')
    }
  }, [addNotification])

  const loadEbooks = useCallback(async () => {
    try {
      const token = getAuthToken()
      const response = await fetch('/books/ebooks', {
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        }
      })
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data?.message || 'Unable to load e-books')
      }
      setEbooks(Array.isArray(data?.ebooks) ? data.ebooks : [])
    } catch (err) {
      console.error('[StudentDashboard] loadEbooks error', err)
      addNotification('Unable to load e-books.')
    }
  }, [addNotification, getAuthToken])

  useEffect(() => {
    const token = getAuthToken()
    const storedRole = getStoredUserRole()
    const tokenRole = decodeTokenRole(token)
    const role = storedRole || tokenRole

    if (!token || isJwtExpired(token)) {
      redirectToLogin()
      return
    }

    if (role && role !== 'student') {
      console.warn('[StudentDashboard] wrong role', { role })
      setAuthStatus('unauthorized')
      setAuthMessage('Unauthorized access. Login with a student account to continue.')
      setLoading(false)
      return
    }

    setAuthStatus('authorized')
    setLoading(true)
    setFetchError('')

    async function loadDashboardData() {
      await Promise.allSettled([loadProfile(), loadPopularBooks(), loadEbooks()])
      const currentToken = getAuthToken()
      if (currentToken && !isJwtExpired(currentToken)) {
        await loadLoans()
      }
    }

    loadDashboardData().finally(() => setLoading(false))
  }, [decodeTokenRole, getAuthToken, loadLoans, loadProfile, loadPopularBooks, loadEbooks, redirectToLogin])

  const stats = useMemo(
    () => {
      const active = loans.filter(l => isApprovedLoan(l)).length
      const totalLoanCount = loans.filter(l => !l.is_request).length
      const overdue = loans.filter(l => isApprovedLoan(l) && l.due_date && new Date(l.due_date) < new Date()).length
      const returned = loans.filter(l => l.returned).length
      const overdueRate = totalLoanCount > 0 ? Math.round((overdue / totalLoanCount) * 100) : 0
      return [
        { label: 'Borrowed', value: active, type: 'green' },
        { label: 'Overdue', value: overdue, type: 'red' },
        { label: 'Overdue Rate', value: `${overdueRate}%`, type: 'gold' },
        { label: 'Returned', value: returned, type: 'blue' },
        { label: 'Total Loans', value: totalLoanCount, type: 'purple' }
      ]
    },
    [loans]
  )

  const activeBorrowedBookIds = useMemo(
    () => loans.filter((loan) => isApprovedLoan(loan) || isPendingRequest(loan)).map((loan) => loan.book_id),
    [loans]
  )

  const studentNumber = profile?.student_number || (isRegistrationStudentId(profile?.student_id) ? profile.student_id : '')
  const studentName = profile?.full_name || profile?.name || ''
  const studentEmail = profile?.email || ''
  const studentInitials = getInitials(studentName)

  const openEditProfile = () => {
    setEditProfileForm({
      full_name: studentName,
      email: studentEmail
    })
    setEditProfileErrors({})
    setShowEditProfile(true)
  }

  const validateEditProfile = () => {
    const errors = {}
    const fullName = editProfileForm.full_name.trim()
    const email = editProfileForm.email.trim()

    if (!fullName) {
      errors.full_name = 'Full name is required.'
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
      errors.email = 'Enter a valid email address.'
    }

    setEditProfileErrors(errors)
    return Object.keys(errors).length === 0
  }

  async function handleSaveProfile(event) {
    event.preventDefault()
    if (!validateEditProfile()) {
      return
    }

    setSavingProfile(true)
    try {
      const token = getAuthToken()
      const response = await fetch('/api/student/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          full_name: editProfileForm.full_name.trim(),
          email: editProfileForm.email.trim()
        })
      })
      const data = await response.json().catch(() => ({}))
      if (!response.ok) {
        setEditProfileErrors({ form: data?.message || 'Unable to update profile.' })
        return
      }

      if (data?.profile) {
        setProfile(data.profile)
      } else {
        await loadProfile()
      }
      setShowEditProfile(false)
      addNotification('Profile updated successfully.')
    } catch (err) {
      console.error('[StudentDashboard] save profile error', err)
      setEditProfileErrors({ form: 'Unable to update profile. Please try again.' })
    } finally {
      setSavingProfile(false)
    }
  }

  async function handleChangePassword(event) {
    event.preventDefault()
    try {
      const response = await fetch('/api/auth/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(passwordForm)
      })
      if (response.ok) {
        setPasswordForm({ old_password: '', new_password: '' })
        addNotification('Password changed successfully.')
      } else {
        addNotification('Password change failed.')
      }
    } catch {
      addNotification('Error changing password.')
    }
  }

  async function handleReturnLoan(loan) {
    try {
      await returnBook(Number(loan.loan_id))
      await loadLoans()
      addNotification(`Returned "${loan.book_title || 'book'}" successfully.`)
    } catch (err) {
      await loadLoans()
      addNotification(err?.response?.data?.message || 'Unable to return this book.')
    }
  }

  async function handleDownloadEbook(ebook) {
    try {
      const token = getAuthToken()
      const response = await fetch(`/books/ebooks/${ebook.ebook_id}/download`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data?.message || 'Unable to download e-book')
      }
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = ebook.original_filename || `${ebook.title}.${ebook.file_type || 'pdf'}`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      addNotification(err?.message || 'Unable to download e-book.')
    }
  }

  function renderPage() {
    if (activePage === 'overview') {
      return (
        <>
          <div className="stats-grid">
            {stats.map((stat) => {
              const StatIcon = getStatIcon(stat.label)
              return (
                <div key={stat.label} className={`stat ${stat.type}`}>
                  <div className="stat-label">{stat.label}</div>
                  <div className="stat-num">{stat.value}</div>
                  <div className="stat-sub">Total</div>
                  <div className="stat-icon">
                    <StatIcon size={34} strokeWidth={1.8} aria-hidden="true" />
                  </div>
                </div>
              )
            })}
          </div>
          <div className="grid2">
            <div className="card">
              <div className="card-hdr"><div className="card-title">Welcome Back!</div></div>
              <div className="student-id-hero">
                <div className="student-id-label">Student ID</div>
                <div className="student-id-value">{displayValue(studentNumber)}</div>
              </div>
              <p>View your borrowed books, track due dates, and manage your account from this dashboard.</p>
              <p style={{ marginTop: '12px', fontSize: '12px', color: 'var(--muted)' }}>
                {studentName || 'Student'}{studentNumber ? ` - ${studentNumber}` : ''}
              </p>
            </div>
            <div className="card">
              <div className="card-hdr"><div className="card-title">Quick Actions</div></div>
              <div style={{ display: 'grid', gap: '10px' }}>
                <button className="btn btn-green" type="button" onClick={() => setActivePage('books')}>View My Books</button>
                <button className="btn btn-outline" type="button" onClick={() => setActivePage('reading')}>Reading History</button>
                <button className="btn btn-outline" type="button" onClick={() => setActivePage('history')}>Borrowing History</button>
                <button className="btn btn-outline" type="button" onClick={() => setActivePage('profile')}>View Profile</button>
              </div>
            </div>
          </div>
          {loans.filter(l => isApprovedLoan(l) || isPendingRequest(l)).length > 0 && (
            <div className="card">
              <div className="card-hdr"><div className="card-title">Current Requests and Loans</div></div>
              <div className="admin-table-container">
                <table>
                  <thead>
                    <tr><th>Book</th><th>Requested/Issued</th><th>Due Date</th><th>Status</th><th>Fine</th><th>Action</th></tr>
                  </thead>
                  <tbody>
                    {loans.filter(l => isApprovedLoan(l) || isPendingRequest(l)).slice(0, 5).map((loan) => {
                      const isOverdue = isApprovedLoan(loan) && loan.due_date && new Date(loan.due_date) < new Date()
                      return (
                        <tr key={loan.loan_id}>
                          <td>{loan.book_title || loan.book_id}</td>
                          <td>{loan.issue_date ? new Date(loan.issue_date).toLocaleDateString() : ''}</td>
                          <td>{loan.due_date ? new Date(loan.due_date).toLocaleDateString() : 'Waiting approval'}</td>
                          <td style={{ color: isPendingRequest(loan) ? 'var(--gold)' : isOverdue ? 'var(--red)' : 'var(--green)' }}>
                            {isPendingRequest(loan) ? 'Pending' : isOverdue ? 'Overdue' : 'Approved'}
                          </td>
                          <td>{loan.fine_amount > 0 ? `$${Number(loan.fine_amount).toFixed(2)}` : '-'}</td>
                          <td>
                            {isApprovedLoan(loan) ? (
                              <button className="btn btn-gold btn-sm" type="button" onClick={() => handleReturnLoan(loan)}>Return</button>
                            ) : (
                              <span style={{ color: 'var(--muted)' }}>Awaiting librarian</span>
                            )}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )
    }

    if (activePage === 'books') {
      const borrowedLoans = loans.filter(l => isApprovedLoan(l) || isPendingRequest(l) || isRejectedRequest(l))
      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">My Borrow Requests and Books ({borrowedLoans.length})</div></div>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr><th>Book Title</th><th>Requested/Issued</th><th>Due Date</th><th>Days/Fine</th><th>Status</th><th>Action</th></tr>
              </thead>
              <tbody>
                {borrowedLoans.map((loan) => {
                  const daysLeft = loan.due_date ? Math.ceil((new Date(loan.due_date) - new Date()) / (1000 * 60 * 60 * 24)) : null
                  const isOverdue = isApprovedLoan(loan) && daysLeft < 0
                  return (
                    <tr key={loan.loan_id}>
                      <td>{loan.book_title || loan.book_id}</td>
                      <td>{loan.issue_date ? new Date(loan.issue_date).toLocaleDateString() : ''}</td>
                      <td>{loan.due_date ? new Date(loan.due_date).toLocaleDateString() : '-'}</td>
                      <td style={{ color: isPendingRequest(loan) ? 'var(--gold)' : isRejectedRequest(loan) ? 'var(--red)' : isOverdue ? 'var(--red)' : daysLeft < 3 ? 'var(--gold)' : 'var(--green)', fontWeight: 'bold' }}>
                        {isPendingRequest(loan) ? 'Waiting approval' : isRejectedRequest(loan) ? (loan.rejection_reason || 'Rejected') : isOverdue ? `${Math.abs(daysLeft)} days overdue - $${Number(loan.fine_amount || 0).toFixed(2)}` : `${daysLeft} days`}
                      </td>
                      <td>{isPendingRequest(loan) ? 'Pending' : isRejectedRequest(loan) ? 'Rejected' : isOverdue ? 'Overdue' : daysLeft < 3 ? 'Due Soon' : 'Approved'}</td>
                      <td>
                        {isApprovedLoan(loan) ? (
                          <button className="btn btn-gold btn-sm" type="button" onClick={() => handleReturnLoan(loan)}>Return</button>
                        ) : (
                          <span style={{ color: 'var(--muted)' }}>No action</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )
    }

    if (activePage === 'catalog') {
      return (
        <BookSearch
          initialKeyword={searchQuery}
          borrowedBookIds={activeBorrowedBookIds}
          onBorrowed={async (book) => {
            await loadLoans()
            addNotification(`Borrow request for "${book.title}" was submitted.`)
          }}
        />
      )
    }

    if (activePage === 'ebooks') {
      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">E-book Library</div></div>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr><th>Title</th><th>Book</th><th>Type</th><th>Size</th><th>Access</th></tr>
              </thead>
              <tbody>
                {ebooks.length === 0 ? (
                  <tr><td colSpan="5" style={{ color: 'var(--muted)', padding: '18px', textAlign: 'center' }}>No e-books available yet.</td></tr>
                ) : (
                  ebooks.map((ebook) => (
                    <tr key={ebook.ebook_id}>
                      <td>{ebook.title}</td>
                      <td>{ebook.book_title}</td>
                      <td>{String(ebook.file_type).toUpperCase()}</td>
                      <td>{Math.ceil((ebook.file_size || 0) / 1024)} KB</td>
                      <td><button className="btn btn-green btn-sm" type="button" onClick={() => handleDownloadEbook(ebook)}>Download</button></td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )
    }

    if (activePage === 'reading') {
      const readingHistory = loans
      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">Reading History</div></div>
          <p>Review your student eLibrary history for all borrowed books, including active reads and completed returns.</p>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr>
                  <th>Book Title</th>
                  <th>Issued</th>
                  <th>Returned</th>
                  <th>Duration</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {readingHistory.length === 0 ? (
                  <tr><td colSpan="5" style={{ color: 'var(--muted)', padding: '18px', textAlign: 'center' }}>No reading history found yet.</td></tr>
                ) : (
                  readingHistory.map((loan) => {
                    const issuedDate = new Date(loan.issue_date)
                    const returnedDate = loan.return_date ? new Date(loan.return_date) : null
                    const durationDays = Math.ceil(((returnedDate || new Date()) - issuedDate) / (1000 * 60 * 60 * 24))
                    const isOverdue = !loan.returned && new Date(loan.due_date) < new Date()
                    return (
                      <tr key={loan.loan_id}>
                        <td>{loan.book_title || loan.book_id}</td>
                        <td>{issuedDate.toLocaleDateString()}</td>
                        <td>{returnedDate ? returnedDate.toLocaleDateString() : 'In progress'}</td>
                        <td>{durationDays} day{durationDays === 1 ? '' : 's'}</td>
                        <td style={{ color: loan.returned ? 'var(--blue)' : isOverdue ? 'var(--red)' : 'var(--green)' }}>
                          {loan.returned ? 'Returned' : isOverdue ? 'Overdue' : 'In progress'}
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )
    }

    if (activePage === 'popular') {
      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">Top Borrowed Books</div></div>
          <p>These are the most borrowed books in the system, with current availability status.</p>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Author</th>
                  <th>Borrowed</th>
                  <th>Availability</th>
                </tr>
              </thead>
              <tbody>
                {popularBooks.length === 0 ? (
                  <tr><td colSpan="4" style={{ color: 'var(--muted)', padding: '18px', textAlign: 'center' }}>No data available.</td></tr>
                ) : (
                  popularBooks.map((book) => (
                    <tr key={book.book_id || book.id}>
                      <td>{book.title}</td>
                      <td>{book.author}</td>
                      <td>{book.borrow_count ?? 0}</td>
                      <td style={{ color: book.status === 'borrowed' || book.available_copies === 0 ? 'var(--red)' : 'var(--green)' }}>
                        {book.status === 'borrowed' || book.available_copies === 0 ? 'Borrowed' : 'Available'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )
    }

    if (activePage === 'history') {
      const history = loans.filter(l => l.returned)
      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">Borrowing History ({history.length})</div></div>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr><th>Book Title</th><th>Issued</th><th>Returned</th><th>Duration</th></tr>
              </thead>
              <tbody>
                {history.map((loan) => {
                  const duration = Math.ceil((new Date(loan.return_date || loan.due_date) - new Date(loan.issue_date)) / (1000 * 60 * 60 * 24))
                  return (
                    <tr key={loan.loan_id}>
                      <td>{loan.book_title || loan.book_id}</td>
                      <td>{new Date(loan.issue_date).toLocaleDateString()}</td>
                      <td>{loan.return_date ? new Date(loan.return_date).toLocaleDateString() : ''}</td>
                      <td>{duration} days</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )
    }

    if (activePage === 'profile') {
      return (
        <div className="profile-layout">
          <div className="card profile-summary-card">
            <div className="profile-avatar">{studentInitials}</div>
            <div className="profile-name">{studentName || 'Student'}</div>
            <div className="profile-email">{displayValue(studentEmail)}</div>
            <div className="profile-id-panel">
              <div className="student-id-label">Student ID</div>
              <div className="student-id-value">{displayValue(studentNumber)}</div>
            </div>
          </div>

          <div className="card">
            <div className="card-hdr">
              <div className="card-title">Student Profile</div>
              <button className="btn btn-green btn-sm" type="button" onClick={openEditProfile}>Edit Profile</button>
            </div>
            <div className="profile-detail-grid">
              <div><span>Student ID</span><strong>{displayValue(studentNumber)}</strong></div>
              <div><span>Full Name</span><strong>{displayValue(studentName)}</strong></div>
              <div><span>Email Address</span><strong>{displayValue(studentEmail)}</strong></div>
              <div><span>Department / Program</span><strong>{displayValue(profile?.department)}</strong></div>
              <div><span>Year Level</span><strong>{displayValue(profile?.year_level)}</strong></div>
              <div><span>Last Login</span><strong>{formatDate(profile?.last_login)}</strong></div>
            </div>
          </div>
        </div>
      )
    }

    if (activePage === 'password') {
      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">Change Password</div></div>
          <form className="admin-form" style={{ flexDirection: 'column' }} onSubmit={handleChangePassword}>
            <div className="fgroup">
              <label>Current password</label>
              <input type="password" value={passwordForm.old_password} onChange={(event) => setPasswordForm({ ...passwordForm, old_password: event.target.value })} placeholder="Current password" />
            </div>
            <div className="fgroup">
              <label>New password</label>
              <input type="password" value={passwordForm.new_password} onChange={(event) => setPasswordForm({ ...passwordForm, new_password: event.target.value })} placeholder="New password" />
            </div>
            <button className="btn btn-green" type="submit">Save password</button>
          </form>
        </div>
      )
    }

    return (
      <div className="card">
        <div className="card-hdr"><div className="card-title">Page unavailable</div></div>
        <p>Unable to render this section. Please refresh or choose another page.</p>
      </div>
    )
  }

  return (
    <div className="student-dashboard-app">
      <div className="sidebar">
        <div className="logo">
          <div className="logo-icon"><Library size={26} strokeWidth={1.8} aria-hidden="true" /></div>
          <div className="logo-title">LibraX</div>
          <div className="logo-sub">Student</div>
        </div>
        <nav className="nav">
          {navSections.map((section) => (
            <div key={section.section}>
              <div className="nav-section">{section.section}</div>
              {section.items.map((item) => {
                const NavIcon = item.icon
                return (
                  <div key={item.id} className={`nav-item ${activePage === item.id ? 'active' : ''}`} onClick={() => setActivePage(item.id)}>
                    <span className="nav-icon"><NavIcon size={17} strokeWidth={1.9} aria-hidden="true" /></span>
                    <span>{item.title}</span>
                    {item.badge && <span className="nav-badge">{item.badge}</span>}
                  </div>
                )
              })}
            </div>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="avatar">{studentInitials}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '12px', color: 'var(--text)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {studentName || 'Student'}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--muted)' }}>{displayValue(studentEmail || studentNumber)}</div>
            </div>
            <button className="icon-button logout-button" type="button" title="Logout" onClick={() => setShowLogoutConfirm(true)}>
              <LogOut size={16} aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>
      {showEditProfile && (
        <div className="modal-overlay" role="presentation" onClick={() => !savingProfile && setShowEditProfile(false)}>
          <div className="profile-modal" role="dialog" aria-modal="true" aria-labelledby="edit-profile-title" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <div id="edit-profile-title" className="modal-title">Edit Profile</div>
                <div className="modal-subtitle">Student ID, department / program, and year level come from your approved registration.</div>
              </div>
              <button className="modal-close" type="button" disabled={savingProfile} onClick={() => setShowEditProfile(false)} aria-label="Close edit profile">
                <X size={16} aria-hidden="true" />
              </button>
            </div>

            <form className="profile-modal-form" onSubmit={handleSaveProfile}>
              {editProfileErrors.form && <div className="form-error">{editProfileErrors.form}</div>}
              <div className="frow">
                <div className="fgroup">
                  <label>Student ID</label>
                  <input value={displayValue(studentNumber)} readOnly />
                </div>
                <div className="fgroup">
                  <label>Department / Program</label>
                  <input value={displayValue(profile?.department)} readOnly />
                </div>
              </div>
              <div className="frow">
                <div className="fgroup">
                  <label>Year Level</label>
                  <input value={displayValue(profile?.year_level)} readOnly />
                </div>
                <div className="fgroup">
                  <label>Last Login</label>
                  <input value={formatDate(profile?.last_login)} readOnly />
                </div>
              </div>
              <div className="fgroup">
                <label>Full Name</label>
                <input
                  value={editProfileForm.full_name}
                  onChange={(event) => setEditProfileForm({ ...editProfileForm, full_name: event.target.value })}
                  autoComplete="name"
                />
                {editProfileErrors.full_name && <div className="field-error">{editProfileErrors.full_name}</div>}
              </div>
              <div className="fgroup">
                <label>Email Address</label>
                <input
                  type="email"
                  value={editProfileForm.email}
                  onChange={(event) => setEditProfileForm({ ...editProfileForm, email: event.target.value })}
                  autoComplete="email"
                />
                {editProfileErrors.email && <div className="field-error">{editProfileErrors.email}</div>}
              </div>
              <div className="modal-actions">
                <button className="btn btn-outline" type="button" disabled={savingProfile} onClick={() => setShowEditProfile(false)}>Cancel</button>
                <button className="btn btn-green" type="submit" disabled={savingProfile}>{savingProfile ? 'Saving...' : 'Save Changes'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
      {showLogoutConfirm && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 2000 }}>
          <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: '12px', padding: '24px', maxWidth: '400px', color: 'var(--text)' }}>
            <div style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px' }}>Confirm Logout</div>
            <div style={{ fontSize: '14px', color: 'var(--muted)', marginBottom: '24px' }}>Are you sure you want to log out?</div>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button onClick={() => setShowLogoutConfirm(false)} style={{ padding: '8px 16px', background: 'var(--bg3)', border: '1px solid var(--border)', color: 'var(--text)', borderRadius: '6px', cursor: 'pointer', fontSize: '13px' }}>Cancel</button>
              <button onClick={handleLogout} style={{ padding: '8px 16px', background: 'var(--red)', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', fontWeight: 500 }}>Logout</button>
            </div>
          </div>
        </div>
      )}
      <div className="main">
        <div className="topbar">
          <div className="page-title">{pageTitles[activePage] || 'Overview'}</div>
          <div className="search-wrap">
            <Search className="search-icon" size={15} strokeWidth={2} aria-hidden="true" />
            <input className="search-input" value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder="Search..." />
          </div>
          <div style={{ position: 'relative' }}>
            <button className="icon-button notification-button" type="button" onClick={() => setShowNotifications(!showNotifications)} aria-label="Notifications">
              <Bell size={18} aria-hidden="true" />
              {notifications.length > 0 && <span className="notif-badge">{notifications.length}</span>}
            </button>
            {showNotifications && (
              <div className="notif-panel">
                <div className="notif-header">Notifications</div>
                <div className="notif-list">
                  {notifications.length === 0 ? (
                    <div style={{ padding: '16px', textAlign: 'center', color: 'var(--muted)' }}>No notifications</div>
                  ) : (
                    notifications.map(notif => (
                      <div key={notif.id} className="notif-item">
                        <div className="notif-text">{notif.text}</div>
                        <button className="icon-button" type="button" onClick={() => removeNotification(notif.id)} aria-label="Dismiss notification">
                          <X size={14} aria-hidden="true" />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
          <div className="avatar">{studentInitials}</div>
        </div>
        <div className="content">
          {authStatus === 'unauthorized' ? (
            <div className="card">
              <div className="card-hdr"><div className="card-title">Unauthorized access</div></div>
              <p>{authMessage || 'You do not have permission to view this dashboard.'}</p>
              <button className="btn btn-outline" type="button" onClick={handleLogout}>Go to Login</button>
            </div>
          ) : loading ? (
            <div className="card">
              <div className="card-hdr"><div className="card-title">Loading Dashboard</div></div>
              <p>Loading your student data. Please wait...</p>
            </div>
          ) : fetchError ? (
            <div className="card">
              <div className="card-hdr"><div className="card-title">Unable to load dashboard</div></div>
              <p>{fetchError}</p>
              <button className="btn btn-outline" type="button" onClick={() => {
                setLoading(true)
                setFetchError('')
                loadProfile()
                  .then(() => {
                    const currentToken = getAuthToken()
                    if (currentToken && !isJwtExpired(currentToken)) {
                      return loadLoans()
                    }
                    return undefined
                  })
                  .finally(() => setLoading(false))
              }}>Retry</button>
            </div>
          ) : (
            renderPage()
          )}
        </div>
      </div>
    </div>
  )
}
