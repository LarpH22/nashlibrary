import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  BarChart3,
  Bell,
  BookOpen,
  BookMarked,
  CheckCircle2,
  CreditCard,
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
import { fetchMostBorrowedBooks, fetchEbooks, downloadEbook, openEbook } from '../books/bookService.js'
import { confirmFinePayment, fetchStudentFines, previewFinePayment } from '../fines/fineService.js'
import { cancelStudentReservation, fetchStudentReservations } from '../reservations/reservationService.js'
import { clearStoredAuth, decodeJwtPayload, getStoredAuthToken, getStoredUserRole, isJwtExpired } from '../../shared/authStorage.js'
import { formatCurrency } from '../../shared/utils/index.js'
import { PasswordChangeForm, getPasswordChangeValidation } from '../../shared/components/PasswordChangeForm.jsx'
import './StudentDashboard.css'

const navSections = [
  {
    section: 'MAIN',
    items: [
      { id: 'overview', icon: BarChart3, title: 'Overview' },
      { id: 'books', icon: BookOpen, title: 'My Borrowed Books' },
      { id: 'popular', icon: Flame, title: 'Top Books' },
      { id: 'catalog', icon: Search, title: 'Search Catalog' },
      { id: 'reservations', icon: BookMarked, title: 'Reservations' },
      { id: 'fines', icon: CreditCard, title: 'Fines' },
      { id: 'reading', icon: BookMarked, title: 'Reading History' },
      { id: 'history', icon: History, title: 'Borrowing History' }
    ]
  },
  {
    section: 'RESOURCES',
    items: [
      { id: 'ebooks', icon: Library, title: 'E-Books' }
    ]
  }
]

const pageTitles = {
  overview: 'Overview',
  books: 'My Borrowed Books',
  ebooks: 'E-Books',
  popular: 'Top Books',
  catalog: 'Search Catalog',
  reservations: 'Reservations',
  fines: 'Fine Management',
  reading: 'Reading History',
  history: 'Borrowing History',
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
const toDateOnly = (value) => {
  if (!value) {
    return null
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return null
  }
  return new Date(date.getFullYear(), date.getMonth(), date.getDate())
}
const daysUntilDue = (dueDate) => {
  const due = toDateOnly(dueDate)
  if (!due) {
    return null
  }
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  return Math.ceil((due - today) / (1000 * 60 * 60 * 24))
}
const isLoanOverdue = (loan) => isApprovedLoan(loan) && daysUntilDue(loan.due_date) < 0
const loanDueStatusLabel = (loan) => {
  if (isPendingRequest(loan)) return 'Pending'
  if (isRejectedRequest(loan)) return 'Rejected'
  if (isLoanOverdue(loan)) return 'Overdue'
  const daysLeft = daysUntilDue(loan.due_date)
  if (daysLeft === 0) return 'Due Today'
  if (daysLeft !== null && daysLeft < 3) return 'Due Soon'
  return 'Approved'
}
const loanDueStatusColor = (loan) => {
  const status = loanDueStatusLabel(loan)
  if (status === 'Overdue' || status === 'Rejected') return 'var(--red)'
  if (status === 'Due Today' || status === 'Due Soon' || status === 'Pending') return 'var(--gold)'
  return 'var(--green)'
}

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
  if (label === 'Unpaid Fines') return CreditCard
  if (label === 'Returned') return CheckCircle2
  return History
}

export function StudentDashboard() {
  const navigate = useNavigate()
  const [activePage, setActivePage] = useState('overview')
  const [loans, setLoans] = useState([])
  const [profile, setProfile] = useState(null)
  const [popularBooks, setPopularBooks] = useState([])
  const [reservations, setReservations] = useState([])
  const [cancellingReservationId, setCancellingReservationId] = useState(null)
  const [fines, setFines] = useState([])
  const [fineSummary, setFineSummary] = useState({ total_unpaid: 0, total_paid: 0, unpaid_count: 0, paid_count: 0, total_count: 0 })
  const [ebooks, setEbooks] = useState([])
  const [ebookPagination, setEbookPagination] = useState({ page: 1, limit: 15, total: 0, total_pages: 1 })
  const [ebookSearch, setEbookSearch] = useState('')
  const [loadingEbooks, setLoadingEbooks] = useState(false)

  // Initialize activePage from URL parameter
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const tabParam = urlParams.get('tab')
    if (tabParam && ['overview', 'catalog', 'books', 'ebooks', 'reservations', 'reading', 'fines', 'history'].includes(tabParam)) {
      setActivePage(tabParam)
    }
  }, [])
  const [payingFineLoanId, setPayingFineLoanId] = useState(null)
  const [paymentFine, setPaymentFine] = useState(null)
  const [paymentStep, setPaymentStep] = useState('options')
  const [paymentPreview, setPaymentPreview] = useState(null)
  const [paymentResult, setPaymentResult] = useState(null)
  const [paymentReceipt, setPaymentReceipt] = useState(null)
  const [paymentReceiptError, setPaymentReceiptError] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [passwordForm, setPasswordForm] = useState({ old_password: '', new_password: '', confirm_password: '' })
  const [passwordError, setPasswordError] = useState('')
  const [passwordSuccess, setPasswordSuccess] = useState('')
  const [passwordSaving, setPasswordSaving] = useState(false)
  const [notifications, setNotifications] = useState([])
  const [showNotifications, setShowNotifications] = useState(false)
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)
  const [loading, setLoading] = useState(true)
  const [fetchError, setFetchError] = useState('')
  const [authStatus, setAuthStatus] = useState('pending')
  const [authMessage, setAuthMessage] = useState('')
  const [showAccountModal, setShowAccountModal] = useState(false)
  const [accountTab, setAccountTab] = useState('profile')
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

  const authFetch = useCallback(async (url, options = {}) => {
    const token = getAuthToken()
    if (!token || isJwtExpired(token)) {
      redirectToLogin()
      return null
    }

    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
      Authorization: `Bearer ${token}`
    }

    const response = await fetch(url, { ...options, headers })
    const data = await response.json().catch(() => ({}))

    if (response.status === 401) {
      console.warn('[StudentDashboard] unauthorized request', { url, message: data?.message || 'Unauthorized' })
      redirectToLogin()
      return null
    }

    return { response, data }
  }, [getAuthToken, redirectToLogin])

  const loadLoans = useCallback(async () => {
    try {
      const result = await authFetch('/api/loans/student')
      if (!result) {
        return
      }
      const { response, data } = result
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
  }, [addNotification, authFetch])

  const loadProfile = useCallback(async () => {
    try {
      const result = await authFetch('/api/students/profile')
      if (!result) {
        return
      }
      const { response, data } = result
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
  }, [addNotification, authFetch])

  const loadPopularBooks = useCallback(async () => {
    try {
      const response = await fetchMostBorrowedBooks(5)
      setPopularBooks(Array.isArray(response?.books) ? response.books : [])
    } catch (err) {
      console.error('[StudentDashboard] loadPopularBooks error', err)
      addNotification('Unable to load the most borrowed books.')
    }
  }, [addNotification])

  const loadFines = useCallback(async () => {
    try {
      const data = await fetchStudentFines()
      setFines(Array.isArray(data?.fines) ? data.fines : [])
      setFineSummary(data?.summary || { total_unpaid: 0, total_paid: 0, unpaid_count: 0, paid_count: 0, total_count: 0 })
    } catch (err) {
      console.error('[StudentDashboard] loadFines error', err)
      addNotification(err?.response?.data?.message || 'Unable to load fines.')
    }
  }, [addNotification])

  const loadReservations = useCallback(async () => {
    try {
      const data = await fetchStudentReservations()
      const nextReservations = Array.isArray(data?.reservations) ? data.reservations : []
      setReservations((previousReservations) => {
        const previousReadyIds = new Set(
          previousReservations
            .filter((reservation) => String(reservation.status || '').toLowerCase() === 'ready')
            .map((reservation) => reservation.reservation_id)
        )
        nextReservations
          .filter((reservation) => String(reservation.status || '').toLowerCase() === 'ready')
          .filter((reservation) => !previousReadyIds.has(reservation.reservation_id))
          .forEach((reservation) => {
            addNotification(`"${reservation.book_title || 'Reserved book'}" is ready for pickup.`)
          })
        return nextReservations
      })
    } catch (err) {
      console.error('[StudentDashboard] loadReservations error', err)
      addNotification(err?.response?.data?.message || 'Unable to load reservations.')
    }
  }, [addNotification])

  const loadEbooks = useCallback(async (page = 1, search = '') => {
    setLoadingEbooks(true)
    try {
      const data = await fetchEbooks({ page, limit: 15, search })
      setEbooks(Array.isArray(data?.ebooks) ? data.ebooks : [])
      setEbookPagination(data?.pagination || { page: 1, limit: 15, total: 0, total_pages: 1 })
    } catch (err) {
      console.error('[StudentDashboard] loadEbooks error', err)
      addNotification('Unable to load e-books.')
    } finally {
      setLoadingEbooks(false)
    }
  }, [addNotification])

  useEffect(() => {
    if (activePage === 'ebooks') {
      loadEbooks(ebookPagination.page, ebookSearch)
    }
  }, [activePage, loadEbooks, ebookPagination.page, ebookSearch])

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
      await Promise.allSettled([loadProfile(), loadPopularBooks(), loadFines(), loadReservations()])
      const currentToken = getAuthToken()
      if (currentToken && !isJwtExpired(currentToken)) {
        await loadLoans()
      }
    }

    loadDashboardData().finally(() => setLoading(false))
  }, [decodeTokenRole, getAuthToken, loadLoans, loadProfile, loadPopularBooks, loadFines, loadReservations, redirectToLogin])

  useEffect(() => {
    if (authStatus !== 'authorized') {
      return undefined
    }

    let refreshInFlight = false
    const refreshLoansAndFines = async () => {
      if (refreshInFlight || document.visibilityState !== 'visible') {
        return
      }
      refreshInFlight = true
      try {
        await Promise.allSettled([loadLoans(), loadFines(), loadReservations()])
      } finally {
        refreshInFlight = false
      }
    }

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        refreshLoansAndFines()
      }
    }

    const intervalId = window.setInterval(refreshLoansAndFines, 30000)
    window.addEventListener('focus', refreshLoansAndFines)
    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      window.clearInterval(intervalId)
      window.removeEventListener('focus', refreshLoansAndFines)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [authStatus, loadLoans, loadFines, loadReservations])

  const stats = useMemo(
    () => {
      const active = loans.filter(l => isApprovedLoan(l)).length
      const totalLoanCount = loans.filter(l => !l.is_request).length
      const overdue = loans.filter(l => isLoanOverdue(l)).length
      const activeReservations = reservations.filter((reservation) => ['active', 'ready'].includes(String(reservation.status || '').toLowerCase())).length
      return [
        { label: 'Borrowed', value: active, type: 'green' },
        { label: 'Overdue', value: overdue, type: 'red' },
        { label: 'Reservations', value: activeReservations, type: 'gold' },
        { label: 'Unpaid Fines', value: formatCurrency(fineSummary.total_unpaid), type: 'gold' },
        { label: 'Total Loans', value: totalLoanCount, type: 'purple' }
      ]
    },
    [loans, reservations, fineSummary.total_unpaid]
  )

  const activeBorrowedBookIds = useMemo(
    () => loans.filter((loan) => isApprovedLoan(loan) || isPendingRequest(loan)).map((loan) => loan.book_id),
    [loans]
  )
  const activeReservedBookIds = useMemo(
    () => reservations.filter((reservation) => ['active', 'ready'].includes(String(reservation.status || '').toLowerCase())).map((reservation) => reservation.book_id),
    [reservations]
  )

  const studentNumber = profile?.student_number || (isRegistrationStudentId(profile?.student_id) ? profile.student_id : '')
  const studentName = profile?.full_name || profile?.name || ''
  const studentEmail = profile?.email || ''
  const studentInitials = getInitials(studentName)

  const openAccountModal = (tab = 'profile') => {
    setAccountTab(tab)
    setPasswordError('')
    setPasswordSuccess('')

    if (tab === 'profile') {
      setEditProfileForm({
        full_name: studentName,
        email: studentEmail
      })
      setEditProfileErrors({})
    }

    setShowAccountModal(true)
  }

  const openEditProfile = () => openAccountModal('profile')

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
      const result = await authFetch('/api/student/profile', {
        method: 'PUT',
        body: JSON.stringify({
          full_name: editProfileForm.full_name.trim(),
          email: editProfileForm.email.trim()
        })
      })
      if (!result) {
        return
      }
      const { response, data } = result
      if (!response.ok) {
        setEditProfileErrors({ form: data?.message || 'Unable to update profile.' })
        return
      }

      if (data?.profile) {
        setProfile(data.profile)
      } else {
        await loadProfile()
      }
      setShowAccountModal(false)
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
    setPasswordError('')
    setPasswordSuccess('')

    const formValidation = getPasswordChangeValidation(passwordForm)
    if (!formValidation.isValid) {
      setPasswordError(formValidation.message)
      return
    }

    setPasswordSaving(true)
    try {
      const result = await authFetch('/api/auth/change-password', {
        method: 'POST',
        body: JSON.stringify(passwordForm)
      })
      if (!result) {
        return
      }
      const { response, data } = result
      if (response.ok) {
        setPasswordForm({ old_password: '', new_password: '', confirm_password: '' })
        setPasswordSuccess('Password updated successfully.')
        addNotification('Password changed successfully.')
      } else {
        setPasswordError(data?.message || 'Password change failed.')
      }
    } catch (error) {
      setPasswordError(error?.message || 'Error changing password.')
    } finally {
      setPasswordSaving(false)
    }
  }

  function updatePasswordField(field, value) {
    setPasswordForm((current) => ({ ...current, [field]: value }))
    setPasswordError('')
    setPasswordSuccess('')
  }

  function handlePayFine(fine) {
    const loanId = Number(fine.loan_id || fine.borrow_id)
    if (!loanId) {
      addNotification('Unable to identify the loan for this fine.')
      return
    }

    setPaymentFine(fine)
    setPaymentStep('options')
    setPaymentPreview(null)
    setPaymentResult(null)
    setPaymentReceipt(null)
    setPaymentReceiptError('')
  }

  function closePaymentModal() {
    if (payingFineLoanId) {
      return
    }
    setPaymentFine(null)
    setPaymentStep('options')
    setPaymentPreview(null)
    setPaymentResult(null)
    setPaymentReceipt(null)
    setPaymentReceiptError('')
  }

  function goBackToPaymentOptions() {
    if (payingFineLoanId) {
      return
    }
    setPaymentStep('options')
    setPaymentPreview(null)
    setPaymentResult(null)
    setPaymentReceipt(null)
    setPaymentReceiptError('')
  }

  function selectCashPayment() {
    setPaymentStep('cash-confirm')
    setPaymentPreview(null)
    setPaymentResult(null)
    setPaymentReceipt(null)
    setPaymentReceiptError('')
  }

  async function selectOnlinePayment() {
    const loanId = Number(paymentFine?.loan_id || paymentFine?.borrow_id)
    if (!loanId) {
      addNotification('Unable to identify the loan for this fine.')
      return
    }

    setPayingFineLoanId(loanId)
    try {
      const result = await previewFinePayment(loanId, 'online')
      setPaymentPreview(result?.payment || result)
      setPaymentStep('online-qr')
      setPaymentReceipt(null)
      setPaymentReceiptError('')
    } catch (err) {
      addNotification(err?.response?.data?.message || 'Unable to generate payment QR.')
    } finally {
      setPayingFineLoanId(null)
    }
  }

  function validateReceiptFile(file) {
    if (!file) {
      return 'Upload a receipt or proof of online payment before submitting.'
    }
    if (file.size <= 0) {
      return 'The selected receipt file is empty.'
    }
    const extension = file.name.split('.').pop()?.toLowerCase()
    if (!['jpg', 'jpeg', 'png', 'pdf'].includes(extension)) {
      return 'Receipt must be a JPG, PNG, or PDF file.'
    }
    if (file.size > 5 * 1024 * 1024) {
      return 'Receipt file must be 5 MB or smaller.'
    }
    return ''
  }

  function handleReceiptChange(event) {
    const file = event.target.files?.[0] || null
    setPaymentReceipt(file)
    setPaymentReceiptError(file ? validateReceiptFile(file) : '')
  }

  async function confirmSelectedPayment(paymentMethod) {
    const loanId = Number(paymentFine?.loan_id || paymentFine?.borrow_id)
    if (!loanId) {
      addNotification('Unable to identify the loan for this fine.')
      return
    }
    if (payingFineLoanId) {
      return
    }

    const receiptError = paymentMethod === 'online' ? validateReceiptFile(paymentReceipt) : ''
    if (receiptError) {
      setPaymentReceiptError(receiptError)
      return
    }

    setPayingFineLoanId(loanId)
    try {
      const paymentReference = paymentMethod === 'online' ? paymentPreview?.payment_reference : ''
      const result = await confirmFinePayment(loanId, paymentMethod, paymentReference, paymentReceipt)
      await Promise.allSettled([loadFines(), loadLoans()])
      setPaymentResult(result?.payment || result)
      setPaymentStep('submitted')
      setPaymentReceipt(null)
      setPaymentReceiptError('')
      addNotification(result?.message || 'Payment request submitted.')
    } catch (err) {
      addNotification(err?.response?.data?.message || 'Unable to submit this payment.')
    } finally {
      setPayingFineLoanId(null)
    }
  }

  async function handleCancelReservation(reservation) {
    setCancellingReservationId(reservation.reservation_id)
    try {
      const response = await cancelStudentReservation(reservation.reservation_id)
      await loadReservations()
      addNotification(response?.message || 'Reservation cancelled.')
    } catch (err) {
      addNotification(err?.response?.data?.message || 'Unable to cancel reservation.')
    } finally {
      setCancellingReservationId(null)
    }
  }

  function renderPage() {
    if (activePage === 'overview') {
      const activeLoans = loans.filter((loan) => isApprovedLoan(loan))
      const overdueLoans = activeLoans.filter((loan) => isLoanOverdue(loan))
      const totalLoanCount = loans.filter((loan) => !loan.is_request).length
      const activeReservationCount = reservations.filter((reservation) => ['active', 'ready'].includes(String(reservation.status || '').toLowerCase())).length
      const borrowLimit = 5
      const borrowLimitPercent = Math.min(100, Math.round((activeLoans.length / borrowLimit) * 100))
      const currentLoans = activeLoans.slice(0, 3)
      const recentActivity = [
        ...overdueLoans.slice(0, 2).map((loan) => ({
          type: 'danger',
          text: 'Book overdue',
          title: loan.book_title || loan.book_id || 'Unknown book',
          date: loan.due_date
        })),
        ...activeLoans.slice(0, 2).map((loan) => ({
          type: 'gold',
          text: 'Borrowed',
          title: loan.book_title || loan.book_id || 'Unknown book',
          date: loan.issue_date
        }))
      ].slice(0, 6)
      const frequencyMax = Math.max(totalLoanCount, 1)
      const loanSegments = [
        { label: 'Borrowed', value: activeLoans.length, color: '#C9A84C' },
        { label: 'Overdue', value: overdueLoans.length, color: '#e05555' }
      ]

      return (
        <div className="overview-v2">
          <div className="stat-grid">
            <div className="scard danger">
              <div className="sc-label">Overdue <AlertTriangle size={14} aria-hidden="true" /></div>
              <div className="sc-val c-red">{overdueLoans.length}</div>
              <div className="sc-sub">{overdueLoans.length > 0 ? 'Overdue fine active' : 'Clear'}</div>
              <div className="sc-bar"><div className="sc-bar-fill danger-fill" style={{ width: overdueLoans.length > 0 ? '100%' : '0%' }} /></div>
            </div>
            <div className="scard">
              <div className="sc-label">Borrowed <BookOpen size={14} aria-hidden="true" /></div>
              <div className="sc-val">{activeLoans.length}</div>
              <div className="sc-sub">Currently active</div>
              <div className="sc-bar"><div className="sc-bar-fill gold-fill" style={{ width: `${borrowLimitPercent}%` }} /></div>
            </div>
            <div className="scard gold">
              <div className="sc-label">Total loans <History size={14} aria-hidden="true" /></div>
              <div className="sc-val c-gold">{totalLoanCount}</div>
              <div className="sc-sub">{formatCurrency(fineSummary.total_unpaid)} fines</div>
              <div className="sc-bar"><div className="sc-bar-fill gold-fill" style={{ width: '100%' }} /></div>
            </div>
          </div>

          <div className="mid-grid">
            <div className="card">
              <div className="card-head">Currently borrowed <span className={`badge ${overdueLoans.length ? 'b-red' : 'b-green'}`}>{overdueLoans.length} overdue</span></div>
              {currentLoans.length === 0 ? (
                <div className="empty-mini">No active borrowed books.</div>
              ) : currentLoans.map((loan) => (
                <div className="book-row" key={loan.loan_id}>
                  <div className="bk-cover gold-cover"><BookOpen size={15} aria-hidden="true" /></div>
                  <div className="book-copy">
                    <div className="bk-title">{loan.book_title || loan.book_id}</div>
                    <div className="bk-meta">Due: {loan.due_date ? new Date(loan.due_date).toLocaleDateString() : '-'}</div>
                  </div>
                  <span className={`badge ${isLoanOverdue(loan) ? 'b-red' : 'b-gold'}`}>{isLoanOverdue(loan) ? 'Overdue' : 'Borrowed'}</span>
                </div>
              ))}
            </div>

            <div className="card">
              <div className="card-head">Loan breakdown</div>
              <div className="donut-wrap">
                <svg width="100" height="100" viewBox="0 0 100 100" aria-hidden="true">
                  <circle cx="50" cy="50" r="36" fill="none" stroke="#ffffff08" strokeWidth="12" />
                  <circle cx="50" cy="50" r="36" fill="none" stroke="#C9A84C" strokeWidth="12" strokeDasharray={`${Math.max(0, activeLoans.length / frequencyMax * 226)} 226`} strokeDashoffset="56" transform="rotate(-90 50 50)" />
                  <circle cx="50" cy="50" r="36" fill="none" stroke="#e05555" strokeWidth="12" strokeDasharray={`${Math.max(0, overdueLoans.length / frequencyMax * 226)} 226`} strokeDashoffset="-102" transform="rotate(-90 50 50)" />
                  <text x="50" y="46" textAnchor="middle" fontSize="18" fontWeight="500" fill="#c0d0e8">{totalLoanCount}</text>
                  <text x="50" y="57" textAnchor="middle" fontSize="8" fill="#3d4f6e">loans</text>
                </svg>
                <div className="legend-list">
                  {loanSegments.map((segment) => (
                    <div className="legend-item" key={segment.label}>
                      <div className="legend-dot" style={{ background: segment.color }} />
                      <span className="legend-lbl">{segment.label}</span>
                      <span className="legend-val">{segment.value}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="thin-rule" />
              <div className="card-head compact">Quick actions</div>
              <div className="dash-action-grid">
                <button className="mini-action" type="button" onClick={() => setActivePage('books')}>My books</button>
                <button className="mini-action" type="button" onClick={() => setActivePage('catalog')}>Catalog</button>
                <button className="mini-action" type="button" onClick={() => setActivePage('fines')}>Fines</button>
                <button className="mini-action" type="button" onClick={() => setActivePage('ebooks')}>E-books</button>
              </div>
            </div>

            <div className="card">
              <div className="card-head">Recent activity <span className="card-head-tag">this month</span></div>
              {recentActivity.length === 0 ? (
                <div className="empty-mini">No activity yet.</div>
              ) : recentActivity.map((item, index) => (
                <div className="activity-item" key={`${item.type}-${item.title}-${index}`}>
                  <div className={`act-dot ${item.type}`} />
                  <div>
                    <div className="act-text">{item.text} <span>{item.title}</span></div>
                    <div className="act-time">{item.date ? new Date(item.date).toLocaleDateString() : 'Recently'}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bottom-grid">
            <div className="card">
              <div className="card-head">Top books in catalog <span className="card-head-tag">trending</span></div>
              {(popularBooks.length ? popularBooks : []).slice(0, 5).map((book, index) => (
                <div className="top-book-item" key={book.book_id || book.id || index}>
                  <div className={`rank ${index < 2 ? 'top' : ''}`}>{index + 1}</div>
                  <div className="bk-cover gold-cover"><BookOpen size={15} aria-hidden="true" /></div>
                  <div className="book-copy">
                    <div className="tb-title">{book.title || 'Untitled'}</div>
                    <div className="tb-genre">{book.category || 'Catalog'} · {book.author || 'Unknown author'}</div>
                  </div>
                  <div className="rating">{book.borrow_count ?? 0} loans</div>
                </div>
              ))}
              {popularBooks.length === 0 && <div className="empty-mini">No top books available.</div>}
            </div>

            <div className="card">
              <div className="card-head">Account status</div>
              <div className="borrow-limit-row">
                <div className="book-copy">
                  <div className="bk-meta">Borrow limit used</div>
                  <div className="prog-track"><div className="prog-fill gold-fill" style={{ width: `${borrowLimitPercent}%` }} /></div>
                </div>
                <div className="limit-count">{activeLoans.length}/{borrowLimit}</div>
              </div>
              <div className="thin-rule" />
              <div className="status-row"><span>Reservations</span><strong>{activeReservationCount} active</strong></div>
              <div className="status-row danger"><span>Overdue books</span><strong>{overdueLoans.length} book{overdueLoans.length === 1 ? '' : 's'}</strong></div>
              <div className="status-row"><span>Unpaid fines</span><strong>{formatCurrency(fineSummary.total_unpaid)}</strong></div>
              <div className="status-row"><span>Account standing</span><span className={`badge ${Number(fineSummary.total_unpaid || 0) > 0 || overdueLoans.length > 0 ? 'b-gold' : 'b-green'}`}>{Number(fineSummary.total_unpaid || 0) > 0 || overdueLoans.length > 0 ? 'Attention' : 'Good'}</span></div>
            </div>
          </div>
        </div>
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
                <tr><th>Book Title</th><th>Requested/Issued</th><th>Due Date</th><th>Days/Fine</th><th>Status</th></tr>
              </thead>
              <tbody>
                {borrowedLoans.map((loan) => {
                  const daysLeft = daysUntilDue(loan.due_date)
                  const isOverdue = isLoanOverdue(loan)
                  const statusLabel = loanDueStatusLabel(loan)
                  return (
                    <tr key={loan.loan_id}>
                      <td>{loan.book_title || loan.book_id}</td>
                      <td>{loan.issue_date ? new Date(loan.issue_date).toLocaleDateString() : ''}</td>
                      <td>{loan.due_date ? new Date(loan.due_date).toLocaleDateString() : '-'}</td>
                      <td style={{ color: loanDueStatusColor(loan), fontWeight: 'bold' }}>
                        {isPendingRequest(loan) ? 'Waiting approval' : isRejectedRequest(loan) ? (loan.rejection_reason || 'Rejected') : isOverdue ? `${Math.abs(daysLeft)} days overdue - ${formatCurrency(loan.fine_amount)}` : daysLeft === 0 ? 'Due today' : `${daysLeft} days`}
                      </td>
                      <td>{statusLabel}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )
    }

    if (activePage === 'ebooks') {
      const formatFileSize = (bytes) => {
        if (!bytes) return '-'
        const sizes = ['B', 'KB', 'MB', 'GB']
        const i = Math.floor(Math.log(bytes) / Math.log(1024))
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
      }

      const getFileTypeBadge = (ebook) => {
        const ext = String(ebook.file_type || ebook.original_filename?.split('.').pop() || '').toLowerCase()
        if (!ext) return <span className="badge badge-muted">Unknown</span>
        if (ext === 'pdf') return <span className="badge badge-red">PDF</span>
        if (ext === 'epub') return <span className="badge badge-blue">EPUB</span>
        return <span className="badge badge-muted">{ext.toUpperCase()}</span>
      }

      const handleOpenEbook = async (ebook) => {
        try {
          const data = await openEbook(ebook.ebook_id)
          const url = data?.ebook?.access_url || ebook.access_url || `/books/ebooks/${ebook.ebook_id}/download`
          window.open(`${url}?disposition=inline`, '_blank', 'noopener,noreferrer')
        } catch (err) {
          addNotification('Unable to open e-book.')
        }
      }

      const handleDownloadEbook = async (ebook) => {
        try {
          const blob = await downloadEbook(ebook.ebook_id)
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = ebook.original_filename || `${ebook.title || `ebook-${ebook.ebook_id}`}.${ebook.file_type || 'pdf'}`
          document.body.appendChild(a)
          a.click()
          window.URL.revokeObjectURL(url)
          document.body.removeChild(a)
        } catch (err) {
          addNotification('Unable to download e-book.')
        }
      }

      return (
        <div className="card ebook-library-card">
          <div className="card-hdr">
            <div className="card-title">E-Books ({ebookPagination.total})</div>
            <div className="ebook-search-actions">
              <div className="ebook-search-field">
                <Search size={14} aria-hidden="true" />
                <input
                  type="text"
                  placeholder="Search e-books..."
                  value={ebookSearch}
                  onChange={(e) => setEbookSearch(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && loadEbooks(1, e.target.value)}
                />
              </div>
              <button className="btn btn-gold btn-sm ebook-search-button" type="button" onClick={() => loadEbooks(1, ebookSearch)}>Search</button>
            </div>
          </div>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Book</th>
                  <th>Type</th>
                  <th>Size</th>
                  <th>Access</th>
                </tr>
              </thead>
              <tbody>
                {loadingEbooks ? (
                  <tr><td colSpan="5" className="empty-cell">Loading e-books...</td></tr>
                ) : ebooks.length === 0 ? (
                  <tr><td colSpan="5" className="empty-cell">No e-books found.</td></tr>
                ) : (
                  ebooks.map((ebook) => (
                    <tr key={ebook.ebook_id}>
                      <td>{ebook.title || ebook.original_filename || 'Untitled'}</td>
                      <td>{ebook.book_title || 'Unknown book'}</td>
                      <td>{getFileTypeBadge(ebook)}</td>
                      <td>{formatFileSize(ebook.file_size)}</td>
                      <td>
                        <div className="ebook-row-actions">
                          <button className="btn btn-gold btn-sm" type="button" onClick={() => handleOpenEbook(ebook)}>Open</button>
                          {ebook.allow_download !== false && (
                            <button className="btn btn-outline btn-sm" type="button" onClick={() => handleDownloadEbook(ebook)}>Download</button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {ebookPagination.total_pages > 1 && (
            <div className="pagination-controls" style={{ marginTop: '16px', textAlign: 'center' }}>
              <button
                className="btn btn-outline btn-sm"
                disabled={ebookPagination.page <= 1}
                onClick={() => loadEbooks(ebookPagination.page - 1, ebookSearch)}
              >
                Previous
              </button>
              <span style={{ margin: '0 16px' }}>
                Page {ebookPagination.page} of {ebookPagination.total_pages}
              </span>
              <button
                className="btn btn-outline btn-sm"
                disabled={ebookPagination.page >= ebookPagination.total_pages}
                onClick={() => loadEbooks(ebookPagination.page + 1, ebookSearch)}
              >
                Next
              </button>
            </div>
          )}
        </div>
      )
    }

    if (activePage === 'catalog') {
      return (
        <BookSearch
          initialKeyword={searchQuery}
          borrowedBookIds={activeBorrowedBookIds}
          reservedBookIds={activeReservedBookIds}
          onBorrowed={async (book) => {
            await loadLoans()
            addNotification(`Borrow request for "${book.title}" was submitted.`)
          }}
          onReserved={async (book, response) => {
            await loadReservations()
            addNotification(response?.message || `Reservation for "${book.title}" was saved.`)
          }}
        />
      )
    }

    if (activePage === 'reservations') {
      const statusLabel = (status) => {
        const normalized = String(status || '').toLowerCase()
        if (normalized === 'ready') return 'Ready for pickup'
        if (normalized === 'active') return 'Queued'
        if (normalized === 'claimed') return 'Claimed'
        if (normalized === 'cancelled') return 'Cancelled'
        if (normalized === 'expired') return 'Expired'
        return status || '-'
      }

      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">My Reservations ({reservations.length})</div></div>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr><th>Book</th><th>Queue</th><th>Status</th><th>Reserved</th><th>Expires</th><th>Action</th></tr>
              </thead>
              <tbody>
                {reservations.length === 0 ? (
                  <tr><td colSpan="6" className="empty-cell">No reservations yet.</td></tr>
                ) : (
                  reservations.map((reservation) => {
                    const status = String(reservation.status || '').toLowerCase()
                    const canCancel = ['active', 'ready'].includes(status)
                    return (
                      <tr key={reservation.reservation_id}>
                        <td>{reservation.book_title || reservation.book_id}</td>
                        <td>{reservation.queue_position || '-'}</td>
                        <td style={{ color: status === 'ready' ? 'var(--green)' : status === 'active' ? 'var(--gold)' : 'var(--muted)' }}>
                          {statusLabel(status)}
                        </td>
                        <td>{reservation.reservation_date ? new Date(reservation.reservation_date).toLocaleDateString() : '-'}</td>
                        <td>{reservation.expiration_date ? new Date(reservation.expiration_date).toLocaleDateString() : '-'}</td>
                        <td>
                          {canCancel ? (
                            <button className="btn btn-outline btn-sm" type="button" disabled={cancellingReservationId === reservation.reservation_id} onClick={() => handleCancelReservation(reservation)}>
                              {cancellingReservationId === reservation.reservation_id ? 'Cancelling...' : 'Cancel'}
                            </button>
                          ) : (
                            <span style={{ color: 'var(--muted)' }}>Closed</span>
                          )}
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

    if (activePage === 'fines') {
      const outstandingFines = fines.filter((fine) => {
        const status = String(fine.status || '').toLowerCase()
        const paymentStatus = String(fine.payment_status || '').toLowerCase()
        return status === 'unpaid' || ['pending', 'pending_verification', 'failed'].includes(paymentStatus)
      })
      const fineHistory = fines.filter((fine) => !outstandingFines.includes(fine))
      const renderFineStatus = (fine) => {
        const paymentStatus = String(fine.payment_status || '').toLowerCase()
        const status = String(fine.status || '').toLowerCase()
        if (paymentStatus === 'pending') return <span className="fine-status pending">Cash Pending</span>
        if (paymentStatus === 'pending_verification') return <span className="fine-status pending">Pending Verification</span>
        if (paymentStatus === 'failed') return <span className="fine-status failed">Rejected</span>
        if (status === 'paid') return <span className="fine-status paid">Paid</span>
        if (status === 'waived') return <span className="fine-status waived">Waived</span>
        if (Number(fine.days_overdue || 0) > 0) return <span className="fine-status overdue">Overdue</span>
        return <span className="fine-status unpaid">Unpaid</span>
      }

      return (
        <>
          <div className="stats-grid fines-stats">
            <div className="stat red">
              <div className="stat-label">Outstanding</div>
              <div className="stat-num">{formatCurrency(fineSummary.total_unpaid)}</div>
              <div className="stat-sub">{fineSummary.unpaid_count || 0} unpaid</div>
            </div>
            <div className="stat green">
              <div className="stat-label">Paid</div>
              <div className="stat-num">{formatCurrency(fineSummary.total_paid)}</div>
              <div className="stat-sub">{fineSummary.paid_count || 0} paid</div>
            </div>
            <div className="stat gold">
              <div className="stat-label">Fine Records</div>
              <div className="stat-num">{fineSummary.total_count || fines.length}</div>
              <div className="stat-sub">All statuses</div>
            </div>
          </div>

          <div className="card">
            <div className="card-hdr"><div className="card-title">Outstanding Fines ({outstandingFines.length})</div></div>
            <div className="admin-table-container">
              <table>
                <thead>
                  <tr><th>Book</th><th>Due Date</th><th>Overdue</th><th>Amount</th><th>Status</th><th>Action</th></tr>
                </thead>
                <tbody>
                  {outstandingFines.length === 0 ? (
                    <tr><td colSpan="6" className="empty-cell">No outstanding fines.</td></tr>
                  ) : (
                    outstandingFines.map((fine) => {
                      const loanId = fine.loan_id || fine.borrow_id
                      const paymentStatus = String(fine.payment_status || '').toLowerCase()
                      const hasPendingPayment = fine.has_pending_payment || ['pending', 'pending_verification'].includes(paymentStatus)
                      return (
                        <tr key={`${loanId}-${fine.fine_id || 'computed'}`}>
                          <td>{fine.book_title || fine.book_id || 'Unknown book'}</td>
                          <td>{fine.due_date ? new Date(fine.due_date).toLocaleDateString() : '-'}</td>
                          <td>{Number(fine.days_overdue || 0)} day{Number(fine.days_overdue || 0) === 1 ? '' : 's'}</td>
                          <td>{formatCurrency(fine.amount || fine.fine_amount)}</td>
                          <td>{renderFineStatus(fine)}</td>
                          <td>
                            <button className="btn btn-green btn-sm" type="button" disabled={payingFineLoanId === Number(loanId) || hasPendingPayment} onClick={() => handlePayFine(fine)}>
                              {hasPendingPayment ? 'Pending' : payingFineLoanId === Number(loanId) ? 'Submitting...' : 'Pay'}
                            </button>
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="card">
            <div className="card-hdr"><div className="card-title">Fine History ({fineHistory.length})</div></div>
            <div className="admin-table-container">
              <table>
                <thead>
                  <tr><th>Book</th><th>Issued</th><th>Paid</th><th>Amount</th><th>Status</th></tr>
                </thead>
                <tbody>
                  {fineHistory.length === 0 ? (
                    <tr><td colSpan="5" className="empty-cell">No fine history yet.</td></tr>
                  ) : (
                    fineHistory.map((fine) => (
                      <tr key={`${fine.loan_id || fine.borrow_id}-${fine.fine_id || fine.status}`}>
                        <td>{fine.book_title || fine.book_id || 'Unknown book'}</td>
                        <td>{fine.issued_date ? new Date(fine.issued_date).toLocaleDateString() : '-'}</td>
                        <td>{fine.paid_date ? new Date(fine.paid_date).toLocaleDateString() : '-'}</td>
                        <td>{formatCurrency(fine.amount || fine.fine_amount)}</td>
                        <td>{renderFineStatus(fine)}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
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
                    const isOverdue = isLoanOverdue(loan)
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
          <PasswordChangeForm
            form={passwordForm}
            onFieldChange={updatePasswordField}
            onSubmit={handleChangePassword}
            error={passwordError}
            success={passwordSuccess}
            submitting={passwordSaving}
          />
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
          <div className="logo-text">
            <div className="logo-title">LIBRASYS</div>
            <div className="logo-sub">Student</div>
          </div>
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
      </div>
      {showAccountModal && (
        <div className="modal-overlay" role="presentation" onClick={() => !savingProfile && !passwordSaving && setShowAccountModal(false)}>
          <div className="profile-modal account-modal" role="dialog" aria-modal="true" aria-labelledby="account-modal-title" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <div id="account-modal-title" className="modal-title">Account Settings</div>
                <div className="modal-subtitle">Manage your profile and password from one place.</div>
              </div>
              <button className="modal-close" type="button" disabled={savingProfile || passwordSaving} onClick={() => setShowAccountModal(false)} aria-label="Close account settings">
                <X size={16} aria-hidden="true" />
              </button>
            </div>
            <div className="account-tabs">
              <button type="button" className={`account-tab-button ${accountTab === 'profile' ? 'active' : ''}`} onClick={() => setAccountTab('profile')}>Profile</button>
              <button type="button" className={`account-tab-button ${accountTab === 'security' ? 'active' : ''}`} onClick={() => setAccountTab('security')}>Security</button>
            </div>

            {accountTab === 'profile' ? (
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
                  <button className="btn btn-outline" type="button" disabled={savingProfile} onClick={() => setShowAccountModal(false)}>Cancel</button>
                  <button className="btn btn-green" type="submit" disabled={savingProfile}>{savingProfile ? 'Saving...' : 'Save Changes'}</button>
                </div>
              </form>
            ) : (
              <PasswordChangeForm
                form={passwordForm}
                onFieldChange={updatePasswordField}
                onSubmit={handleChangePassword}
                error={passwordError}
                success={passwordSuccess}
                submitting={passwordSaving}
                submitLabel="Change Password"
              />
            )}
          </div>
        </div>
      )}
      {paymentFine && (
        <div className="modal-overlay" role="presentation" onClick={closePaymentModal}>
          <div className="profile-modal payment-modal" role="dialog" aria-modal="true" aria-labelledby="payment-modal-title" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <div id="payment-modal-title" className="modal-title">Pay Fine</div>
                <div className="modal-subtitle">{paymentFine.book_title || 'Library fine'} - {formatCurrency(paymentFine.amount || paymentFine.fine_amount)}</div>
              </div>
              <button className="modal-close" type="button" disabled={Boolean(payingFineLoanId)} onClick={closePaymentModal} aria-label="Close payment modal">
                <X size={16} aria-hidden="true" />
              </button>
            </div>

            <div className="payment-modal-body">
              <div className="payment-summary">
                <div><span>Reference</span><strong>{paymentResult?.payment_reference || paymentPreview?.payment_reference || paymentFine.payment_reference || 'Generated after choosing a method'}</strong></div>
                <div><span>Status</span><strong>{paymentResult?.payment_status_label || paymentFine.payment_status_label || 'Unpaid'}</strong></div>
              </div>

              {paymentStep === 'options' && !paymentResult && (
                <div className="payment-option-grid">
                  <button className="payment-option" type="button" disabled={Boolean(payingFineLoanId)} onClick={selectOnlinePayment}>
                    <CreditCard size={22} aria-hidden="true" />
                    <strong>Online Payment</strong>
                    <span>Generate a QR code first. Status changes only after you confirm submission.</span>
                  </button>
                  <button className="payment-option" type="button" disabled={Boolean(payingFineLoanId)} onClick={selectCashPayment}>
                    <CheckCircle2 size={22} aria-hidden="true" />
                    <strong>Walk-in / Cash</strong>
                    <span>Review the cash payment request before setting it as pending.</span>
                  </button>
                </div>
              )}

              {paymentStep === 'cash-confirm' && !paymentResult && (
                <div className="payment-confirm-panel">
                  <div className="status-message">Confirm walk-in or cash payment only if you will settle this fine with a librarian or admin.</div>
                  <div className="modal-actions">
                    <button className="btn btn-outline" type="button" disabled={Boolean(payingFineLoanId)} onClick={goBackToPaymentOptions}>Back</button>
                    <button className="btn btn-green" type="button" disabled={Boolean(payingFineLoanId)} onClick={() => confirmSelectedPayment('cash')}>
                      {payingFineLoanId ? 'Submitting...' : 'Confirm Cash Payment'}
                    </button>
                  </div>
                </div>
              )}

              {paymentStep === 'online-qr' && paymentPreview && !paymentResult && (
                <div className="payment-result">
                  <div className="status-message">Scan the QR code and complete the online transfer. Your fine will stay unpaid until you confirm that the payment was submitted.</div>
                  {paymentPreview.qr_code_data_url && (
                    <div className="payment-qr-wrap">
                      <img src={paymentPreview.qr_code_data_url} alt={`Payment QR for ${paymentPreview.payment_reference}`} />
                      <div className="modal-subtitle">Use GCash or PayMaya with the exact amount and reference.</div>
                    </div>
                  )}
                  <div className="modal-actions">
                    <button className="btn btn-outline" type="button" disabled={Boolean(payingFineLoanId)} onClick={goBackToPaymentOptions}>Back</button>
                    <button className="btn btn-green" type="button" disabled={Boolean(payingFineLoanId)} onClick={() => setPaymentStep('online-receipt')}>
                      Submit Payment
                    </button>
                  </div>
                </div>
              )}

              {paymentStep === 'online-receipt' && paymentPreview && !paymentResult && (
                <div className="payment-confirm-panel">
                  <div className="status-message">Upload your receipt or proof of online payment. The fine will only move to pending verification after this final submit succeeds.</div>
                  <div className="fgroup">
                    <label>Receipt / proof of payment</label>
                    <input type="file" accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf" disabled={Boolean(payingFineLoanId)} onChange={handleReceiptChange} />
                    {paymentReceipt && <div className="modal-subtitle">{paymentReceipt.name}</div>}
                    {paymentReceiptError && <div className="field-error">{paymentReceiptError}</div>}
                  </div>
                  <div className="modal-actions">
                    <button className="btn btn-outline" type="button" disabled={Boolean(payingFineLoanId)} onClick={() => setPaymentStep('online-qr')}>Back</button>
                    <button className="btn btn-green" type="button" disabled={Boolean(payingFineLoanId)} onClick={() => confirmSelectedPayment('online')}>
                      {payingFineLoanId ? 'Submitting...' : 'Submit Receipt'}
                    </button>
                  </div>
                </div>
              )}

              {paymentStep === 'submitted' && paymentResult && (
                <div className="payment-result">
                  <div className="status-message">Payment submitted. Please wait for confirmation before paying again.</div>
                  {paymentResult.qr_code_data_url && (
                    <div className="payment-qr-wrap">
                      <img src={paymentResult.qr_code_data_url} alt={`Payment QR for ${paymentResult.payment_reference}`} />
                      <div className="modal-subtitle">Scan with GCash or PayMaya, then wait for verification.</div>
                    </div>
                  )}
                  <div className="modal-actions">
                    <button className="btn btn-green" type="button" onClick={closePaymentModal}>Done</button>
                  </div>
                </div>
              )}
            </div>
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
          <div className="topbar-user-card">
            <div className="topbar-user-profile" role="button" tabIndex="0" onClick={() => openAccountModal('profile')} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') openAccountModal('profile') }}>
              <div className="avatar">{studentInitials}</div>
              <div className="topbar-user-text">
                <div className="topbar-user-name">{studentName || 'Student'}</div>
                <div className="topbar-user-email">{displayValue(studentEmail || studentNumber)}</div>
              </div>
            </div>
            <button className="topbar-logout-button" type="button" title="Logout" onClick={() => setShowLogoutConfirm(true)} aria-label="Logout">
              <LogOut size={17} aria-hidden="true" />
            </button>
          </div>
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
