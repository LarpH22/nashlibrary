import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Activity, ArrowUpRight, BarChart3, BookOpen, Search, Clock3, Users, Key, Bell, Menu, Power, Repeat, ListChecks, CreditCard, Sparkles, X, Zap } from 'lucide-react'
import api, { normalizeApiError } from '../../shared/api.js'
import { ReturnPlatform } from '../returns/ReturnPlatform.jsx'
import { clearStoredAuth } from '../../shared/authStorage.js'
import { formatCurrency } from '../../shared/utils/index.js'
import { PasswordChangeForm, getPasswordChangeValidation } from '../../shared/components/PasswordChangeForm.jsx'
import { approveReservation, cancelReservation, claimReservation, expireReservations, fetchReservations } from '../reservations/reservationService.js'
import './LibrarianDashboard.css'
import '../../shared/MobileDashboard.css'

const baseNavSections = [
  {
    section: 'MAIN',
    items: [
      { id: 'overview', icon: BarChart3, title: 'Overview' },
      { id: 'issue-return', icon: BookOpen, title: 'Borrow Approvals' },
      { id: 'returns', icon: Repeat, title: 'Returns' },
      { id: 'availability', icon: Search, title: 'Book Availability' },
      { id: 'overdue', icon: Clock3, title: 'Overdue Books' }
    ]
  },
  {
    section: 'RECORDS',
    items: [
      { id: 'students', icon: Users, title: 'Student Records' },
      { id: 'reservations', icon: ListChecks, title: 'Reservations' },
      { id: 'fines', icon: CreditCard, title: 'Fine Payments' },
      { id: 'search', icon: Search, title: 'Search Books' }
    ]
  }
]

const pageTitles = {
  overview: 'Overview',
  'issue-return': 'Borrow Approvals',
  availability: 'Book Availability',
  overdue: 'Overdue Books',
  students: 'Student Records',
  reservations: 'Reservations',
  fines: 'Fine Payments',
  returns: 'Returns Platform',
  search: 'Search Books'
}

const ebookLibraryPageSize = 10
const bookSearchPageSize = 10

function mergeEbooksWithCatalog(ebookRows) {
  return Array.isArray(ebookRows) ? [...ebookRows] : []
}

function apiMessage(error, fallback) {
  return normalizeApiError(error, fallback).message || fallback
}

function ebookDeleteMessage(error) {
  const normalized = normalizeApiError(error)
  if (normalized.status === 409 || normalized.data?.code === 'ebook_in_use') {
    return 'This e-book cannot be deleted because it is currently borrowed or in use.'
  }
  return normalized.message || 'Unable to delete e-book.'
}

const isLoanReturned = (loan) => loan.returned || String(loan.status || '').toLowerCase() === 'returned'

const isLoanOverdue = (loan) => {
  if (isLoanReturned(loan) || !loan.due_date) {
    return false
  }

  const dueDate = new Date(loan.due_date)
  return !Number.isNaN(dueDate.getTime()) && dueDate < new Date()
}

const formatLoanDate = (value) => {
  if (!value) {
    return '-'
  }
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '-' : date.toLocaleDateString()
}

const loanStatusLabel = (loan) => {
  if (isLoanReturned(loan)) return 'Returned'
  if (isLoanOverdue(loan)) return 'Overdue'
  return 'Borrowed'
}

export function LibrarianDashboard() {
  const navigate = useNavigate()
  const [activePage, setActivePage] = useState('overview')
  const [books, setBooks] = useState([])
  const [ebooks, setEbooks] = useState([])
  const [ebookPage, setEbookPage] = useState(1)
  const [ebookLoading, setEbookLoading] = useState(false)
  const [availabilityBooks, setAvailabilityBooks] = useState([])
  const [availabilityFilters, setAvailabilityFilters] = useState({ title: '', isbn: '', availability: '' })
  const [availabilityPagination, setAvailabilityPagination] = useState({ page: 1, limit: 10, total: 0, total_pages: 1 })
  const [availabilityLoading, setAvailabilityLoading] = useState(false)
  const [loans, setLoans] = useState([])
  const [borrowRequests, setBorrowRequests] = useState([])
  const [reservations, setReservations] = useState([])
  const [fines, setFines] = useState([])
  const [fineSummary, setFineSummary] = useState({ total_count: 0, unpaid_count: 0, pending_count: 0, paid_count: 0, total_unpaid: 0, total_paid: 0 })
  const [loadingFines, setLoadingFines] = useState(false)
  const [reservationActionId, setReservationActionId] = useState(null)
  const [students, setStudents] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [bookSearchPage, setBookSearchPage] = useState(1)
  const [requestDueDates, setRequestDueDates] = useState({})
  const [scanForm, setScanForm] = useState({ code: '', student_id: '' })
  const [scanResult, setScanResult] = useState(null)
  const [passwordForm, setPasswordForm] = useState({ old_password: '', new_password: '', confirm_password: '' })
  const [showAccountModal, setShowAccountModal] = useState(false)
  const [accountTab, setAccountTab] = useState('profile')
  const [notifications, setNotifications] = useState([])
  const [showNotifications, setShowNotifications] = useState(false)
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [passwordError, setPasswordError] = useState('')
  const [passwordSuccess, setPasswordSuccess] = useState('')
  const [passwordSaving, setPasswordSaving] = useState(false)
  const [ebookUploadTitle, setEbookUploadTitle] = useState('')
  const [ebookUploadFile, setEbookUploadFile] = useState(null)
  const [ebookUploading, setEbookUploading] = useState(false)

  const addNotification = useCallback((text) => {
    const id = Date.now()
    setNotifications(prev => [...prev, { id, text, timestamp: new Date() }])
  }, [])

  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }, [])

  const safeBooks = useMemo(() => (Array.isArray(books) ? books : []), [books])
  const safeEbooks = useMemo(() => (Array.isArray(ebooks) ? ebooks : []), [ebooks])
  const safeAvailabilityBooks = useMemo(() => (Array.isArray(availabilityBooks) ? availabilityBooks : []), [availabilityBooks])
  const safeLoans = useMemo(() => (Array.isArray(loans) ? loans : []), [loans])
  const safeBorrowRequests = useMemo(() => (Array.isArray(borrowRequests) ? borrowRequests : []), [borrowRequests])
  const safeReservations = useMemo(() => (Array.isArray(reservations) ? reservations : []), [reservations])
  const safeFines = useMemo(() => (Array.isArray(fines) ? fines : []), [fines])
  const safeStudents = useMemo(() => (Array.isArray(students) ? students : []), [students])
  const pendingBorrowRequests = useMemo(() => safeBorrowRequests.filter((request) => request.status === 'pending'), [safeBorrowRequests])
  const activeReservationCount = useMemo(() => safeReservations.filter((reservation) => ['active', 'ready'].includes(String(reservation.status || '').toLowerCase())).length, [safeReservations])
  const pendingFinePayments = useMemo(() => safeFines.filter((fine) => ['pending', 'pending_verification'].includes(String(fine.payment_status || '').toLowerCase())), [safeFines])
  const activeLoans = useMemo(() => safeLoans.filter((loan) => !isLoanReturned(loan)), [safeLoans])
  const overdueLoans = useMemo(() => safeLoans.filter(isLoanOverdue), [safeLoans])
  const navigationSections = useMemo(
    () => baseNavSections.map((section) => {
      const sectionItems = section.section === 'RECORDS'
        ? [
            ...section.items.filter((item) => item.id !== 'search'),
            { id: 'ebooks', icon: BookOpen, title: 'E-books' },
            ...section.items.filter((item) => item.id === 'search')
          ]
        : section.items

      return {
        ...section,
        items: sectionItems.map((item) => (
          item.id === 'overdue'
            ? { ...item, badge: overdueLoans.length > 0 ? String(overdueLoans.length) : '' }
            : item.id === 'reservations'
              ? { ...item, badge: activeReservationCount > 0 ? String(activeReservationCount) : '' }
            : item.id === 'fines'
              ? { ...item, badge: pendingFinePayments.length > 0 ? String(pendingFinePayments.length) : '' }
            : item
        ))
      }
    }),
    [overdueLoans.length, activeReservationCount, pendingFinePayments.length]
  )

  const studentRecords = useMemo(() => {
    const map = new Map()

    safeLoans.forEach((loan) => {
      const userId = loan.user_id ?? loan.student_id
      if (!userId) return

      const existing = map.get(userId) || {
        user_id: userId,
        full_name: loan.student_name || loan.full_name || 'Unknown',
        email: loan.student_email || '',
        status: loan.status || 'Active',
        borrowed_books: 0
      }

      map.set(userId, existing)
    })

    safeLoans.forEach((loan) => {
      const userId = loan.user_id ?? loan.student_id
      if (!userId) return
      const student = map.get(userId)
      if (student && !loan.returned) {
        student.borrowed_books = (student.borrowed_books || 0) + 1
      }
    })

    return Array.from(map.values())
  }, [safeLoans])

  const studentList = safeStudents.length > 0 ? safeStudents : studentRecords

  const handleLogout = () => {
    clearStoredAuth()
    navigate('/login', { replace: true })
  }

  const handleNavSelect = (pageId) => {
    setActivePage(pageId)
    setMobileNavOpen(false)
  }

  const openAccountModal = (tab = 'profile') => {
    setAccountTab(tab)
    setPasswordError('')
    setPasswordSuccess('')
    setShowAccountModal(true)
  }

  const loadBooks = useCallback(async () => {
    try {
      const response = await api.get('/books/')
      setBooks(Array.isArray(response.data) ? response.data : [])
    } catch (error) {
      console.error('Unable to load books:', error)
      setBooks([])
      addNotification('Unable to load books.')
    }
  }, [])

  const loadEbooks = useCallback(async () => {
    setEbookLoading(true)
    try {
      const ebookResponse = await api.get('/api/ebooks')
      setEbooks(mergeEbooksWithCatalog(ebookResponse.data?.ebooks))
    } catch (error) {
      console.error('Unable to load e-books:', error)
      setEbooks([])
      addNotification(apiMessage(error, 'Unable to load e-books.'))
    } finally {
      setEbookLoading(false)
    }
  }, [])

  const loadLoans = useCallback(async () => {
    try {
      const response = await api.get('/api/admin/loans')
      setLoans(Array.isArray(response.data) ? response.data : [])
    } catch (error) {
      console.error('Unable to load loans:', error)
      setLoans([])
      addNotification('Unable to load loans.')
    }
  }, [])

  const loadAvailabilityBooks = useCallback(async () => {
    setAvailabilityLoading(true)
    try {
      const response = await api.get('/api/books/search', {
        params: {
          page: availabilityPagination.page,
          limit: availabilityPagination.limit,
          title: availabilityFilters.title.trim(),
          isbn: availabilityFilters.isbn.trim(),
          availability: availabilityFilters.availability
        }
      })
      setAvailabilityBooks(Array.isArray(response.data?.books) ? response.data.books : [])
      const pagination = response.data?.pagination || {}
      setAvailabilityPagination(prev => ({
        page: Number(pagination.page || prev.page || 1),
        limit: Number(pagination.limit || prev.limit || 10),
        total: Number(pagination.total || 0),
        total_pages: Math.max(1, Number(pagination.total_pages || 1))
      }))
    } catch (error) {
      console.error('Unable to load availability page:', error)
      setAvailabilityBooks([])
      addNotification('Unable to load book availability.')
    } finally {
      setAvailabilityLoading(false)
    }
  }, [availabilityFilters, availabilityPagination.page, availabilityPagination.limit])

  const loadStudents = useCallback(async () => {
    try {
      const response = await api.get('/api/admin/students')
      setStudents(Array.isArray(response.data) ? response.data : [])
    } catch (error) {
      console.error('Unable to load students:', error)
      setStudents([])
      addNotification('Unable to load students.')
    }
  }, [])

  const loadBorrowRequests = useCallback(async () => {
    try {
      const response = await api.get('/books/borrow-requests')
      setBorrowRequests(Array.isArray(response.data) ? response.data : [])
    } catch (error) {
      console.error('Unable to load borrow requests:', error)
      setBorrowRequests([])
      addNotification('Unable to load borrow requests.')
    }
  }, [])

  const loadReservations = useCallback(async () => {
    try {
      const response = await fetchReservations()
      setReservations(Array.isArray(response?.reservations) ? response.reservations : [])
    } catch (error) {
      console.error('Unable to load reservations:', error)
      setReservations([])
      addNotification(apiMessage(error, 'Unable to load reservations.'))
    }
  }, [])

  const loadFines = useCallback(async () => {
    setLoadingFines(true)
    try {
      const response = await api.get('/api/fines/admin')
      setFines(Array.isArray(response.data?.fines) ? response.data.fines : [])
      setFineSummary(response.data?.summary || { total_count: 0, unpaid_count: 0, pending_count: 0, paid_count: 0, total_unpaid: 0, total_paid: 0 })
    } catch (error) {
      console.error('Unable to load fines:', error)
      addNotification(apiMessage(error, 'Unable to load fine payments.'))
    } finally {
      setLoadingFines(false)
    }
  }, [addNotification])

  useEffect(() => {
    loadBooks()
    loadEbooks()
    loadLoans()
    loadBorrowRequests()
    loadReservations()
    loadFines()
    loadStudents()
  }, [loadBooks, loadEbooks, loadLoans, loadBorrowRequests, loadReservations, loadFines, loadStudents])

  useEffect(() => {
    loadAvailabilityBooks()
  }, [loadAvailabilityBooks])

  useEffect(() => {
    const realEbooks = safeEbooks.filter(e => !e.is_catalog_only)
    const totalPages = Math.max(1, Math.ceil(realEbooks.length / ebookLibraryPageSize))
    setEbookPage((currentPage) => Math.min(currentPage, totalPages))
  }, [safeEbooks])

  const stats = useMemo(
    () => [
      { label: 'Books', value: safeBooks.length, type: 'blue', icon: BookOpen },
      { label: 'Pending Requests', value: pendingBorrowRequests.length, type: 'gold', icon: ListChecks },
      { label: 'Reservations', value: activeReservationCount, type: 'gold', icon: ListChecks },
      { label: 'Active Loans', value: activeLoans.length, type: 'green', icon: Repeat },
      { label: 'Overdue', value: overdueLoans.length, type: 'red', icon: Clock3 },
      { label: 'Fine Reviews', value: pendingFinePayments.length, type: 'gold', icon: CreditCard },
      { label: 'Students', value: studentList.length, type: 'purple', icon: Users }
    ],
    [safeBooks, pendingBorrowRequests, activeReservationCount, activeLoans.length, overdueLoans.length, pendingFinePayments.length, studentList]
  )

  async function handleApproveRequest(requestId) {
    const dueDate = requestDueDates[requestId]
    if (!dueDate) {
      addNotification('Set a due date before approving this request.')
      return
    }

    try {
      await api.post(`/books/borrow-requests/${requestId}/approve`, {
        due_date: dueDate
      })
      setRequestDueDates((prev) => {
        const next = { ...prev }
        delete next[requestId]
        return next
      })
      await Promise.allSettled([loadBorrowRequests(), loadLoans(), loadBooks(), loadAvailabilityBooks(), loadReservations()])
      addNotification('Borrow request approved.')
    } catch (error) {
      console.error('Error approving request:', error)
      await Promise.allSettled([loadBorrowRequests(), loadLoans(), loadBooks(), loadAvailabilityBooks(), loadReservations()])
      addNotification(error?.response?.data?.message || 'Failed to approve request.')
    }
  }

  async function handleRejectRequest(requestId) {
    try {
      await api.post(`/books/borrow-requests/${requestId}/reject`, {
        reason: 'Rejected by librarian'
      })
      await loadBorrowRequests()
      addNotification('Borrow request rejected.')
    } catch (error) {
      console.error('Error rejecting request:', error)
      await loadBorrowRequests()
      addNotification(error?.response?.data?.message || 'Failed to reject request.')
    }
  }

  async function handleLookupScan(event) {
    event.preventDefault()
    if (!scanForm.code.trim()) {
      addNotification('Scan or enter a barcode/QR value first.')
      return
    }
    try {
      const response = await api.get('/books/scan', { params: { code: scanForm.code.trim() } })
      setScanResult(response.data?.copy || null)
      addNotification('Book copy found.')
    } catch (error) {
      setScanResult(null)
      addNotification(error?.response?.data?.message || 'Scanned copy was not found.')
    }
  }

  async function handleIssueByScan() {
    if (!scanForm.code.trim() || !scanForm.student_id) {
      addNotification('Barcode/QR value and Student ID are required.')
      return
    }
    try {
      await api.post('/books/borrow-by-scan', {
        code: scanForm.code.trim(),
        student_id: Number(scanForm.student_id)
      })
      setScanForm({ code: '', student_id: '' })
      setScanResult(null)
      await Promise.allSettled([loadLoans(), loadBooks(), loadAvailabilityBooks(), loadReservations()])
      addNotification('Book issued from scan.')
    } catch (error) {
      await Promise.allSettled([loadLoans(), loadBooks(), loadAvailabilityBooks(), loadReservations()])
      addNotification(error?.response?.data?.message || 'Failed to issue scanned copy.')
    }
  }

  async function handleReservationAction(reservationId, action) {
    setReservationActionId(reservationId)
    try {
      let response
      if (action === 'approve') {
        response = await approveReservation(reservationId)
      } else if (action === 'claim') {
        response = await claimReservation(reservationId)
      } else {
        response = await cancelReservation(reservationId)
      }
      await Promise.allSettled([loadReservations(), loadLoans(), loadBooks(), loadAvailabilityBooks()])
      addNotification(response?.message || 'Reservation updated.')
    } catch (error) {
      await loadReservations()
      addNotification(apiMessage(error, 'Unable to update reservation.'))
    } finally {
      setReservationActionId(null)
    }
  }

  async function handleExpireReservations() {
    try {
      const response = await expireReservations()
      await Promise.allSettled([loadReservations(), loadBooks(), loadAvailabilityBooks()])
      addNotification(response?.message || 'Expired reservations removed.')
    } catch (error) {
      addNotification(apiMessage(error, 'Unable to remove expired reservations.'))
    }
  }

  async function handleDownloadEbook(ebook) {
    if (ebook.is_catalog_only) {
      return
    }

    try {
      const response = await api.get(`/api/ebooks/${ebook.ebook_id}/download`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(response.data)
      const link = document.createElement('a')
      link.href = url
      link.download = ebook.original_filename || `${ebook.title}.${ebook.file_type || 'pdf'}`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      addNotification(apiMessage(error, 'Unable to download e-book.'))
    }
  }

  async function handleDeleteEbook(ebook) {
    if (!window.confirm(`Delete e-book '${ebook.title}'? This cannot be undone.`)) {
      return
    }

    try {
      await api.delete(`/api/ebooks/${ebook.ebook_id}`)
      addNotification('E-book deleted successfully.')
      await loadEbooks()
    } catch (error) {
      addNotification(ebookDeleteMessage(error))
    }
  }

  async function handleUploadEbook() {
    if (!ebookUploadFile) {
      addNotification('Please choose a PDF or EPUB file to upload.')
      return
    }

    const formData = new FormData()
    formData.append('title', ebookUploadTitle.trim())
    formData.append('ebook', ebookUploadFile)

    setEbookUploading(true)
    try {
      await api.post('/api/ebooks', formData)
      addNotification('E-book uploaded successfully.')
      setEbookUploadTitle('')
      setEbookUploadFile(null)
      await loadEbooks()
    } catch (error) {
      addNotification(apiMessage(error, 'Unable to upload e-book.'))
    } finally {
      setEbookUploading(false)
    }
  }

  async function handleSendReminders(type) {
    try {
      const url = type === 'overdue' ? '/api/reminders/send-overdue-reminders' : '/api/reminders/send-due-reminders'
      const response = await api.post(url)
      const data = response.data?.data || {}
      addNotification(`Reminders sent: ${data.sent || 0}, failed: ${data.failed || 0}.`)
    } catch (error) {
      addNotification(error?.response?.data?.message || 'Failed to send reminders.')
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
      const response = await api.post('/api/admin/password', passwordForm)
      const successMessage = response.data?.message
      if (response.status === 200 && successMessage && successMessage.toLowerCase().includes('updated successfully')) {
        setPasswordForm({ old_password: '', new_password: '', confirm_password: '' })
        setPasswordError('')
        setPasswordSuccess('Password updated successfully.')
      } else {
        const errorMsg = successMessage || 'Password change failed. Please try again.'
        console.warn('Password change did not succeed:', response.status, response.data)
        setPasswordError(errorMsg)
      }
    } catch (error) {
      console.error('Error changing password:', error.response?.status, error.response?.data)
      const errorMsg = error.response?.data?.message || error.message || 'Password change failed. Please try again.'
      setPasswordError(errorMsg)
    } finally {
      setPasswordSaving(false)
    }
  }

  function updatePasswordField(field, value) {
    setPasswordForm((current) => ({ ...current, [field]: value }))
    setPasswordError('')
    setPasswordSuccess('')
  }

  function updateAvailabilityFilter(field, value) {
    setAvailabilityFilters(prev => ({ ...prev, [field]: value }))
    setAvailabilityPagination(prev => ({ ...prev, page: 1 }))
  }

  function setAvailabilityPage(page) {
    setAvailabilityPagination(prev => ({
      ...prev,
      page: Math.min(Math.max(1, page), Math.max(1, prev.total_pages || 1))
    }))
  }

  function availabilityPageNumbers() {
    const totalPages = Math.max(1, availabilityPagination.total_pages || 1)
    const currentPage = Math.min(Math.max(1, availabilityPagination.page || 1), totalPages)
    const start = Math.max(1, currentPage - 2)
    const end = Math.min(totalPages, start + 4)
    const normalizedStart = Math.max(1, end - 4)
    const pages = []
    for (let page = normalizedStart; page <= end; page += 1) {
      pages.push(page)
    }
    return pages
  }

  function setEbookLibraryPage(page) {
    const realEbooks = safeEbooks.filter(e => !e.is_catalog_only)
    const totalPages = Math.max(1, Math.ceil(realEbooks.length / ebookLibraryPageSize))
    setEbookPage(Math.min(Math.max(1, page), totalPages))
  }

  function ebookPageNumbers() {
    const realEbooks = safeEbooks.filter(e => !e.is_catalog_only)
    const totalPages = Math.max(1, Math.ceil(realEbooks.length / ebookLibraryPageSize))
    const currentPage = Math.min(Math.max(1, ebookPage || 1), totalPages)
    const start = Math.max(1, currentPage - 2)
    const end = Math.min(totalPages, start + 4)
    const normalizedStart = Math.max(1, end - 4)
    const pages = []
    for (let page = normalizedStart; page <= end; page += 1) {
      pages.push(page)
    }
    return pages
  }

  function setSearchBookPage(page, totalPages) {
    setBookSearchPage(Math.min(Math.max(1, page), Math.max(1, totalPages || 1)))
  }

  function searchBookPageNumbers(totalPages, currentPage) {
    const normalizedTotal = Math.max(1, totalPages || 1)
    const normalizedCurrent = Math.min(Math.max(1, currentPage || 1), normalizedTotal)
    const start = Math.max(1, normalizedCurrent - 2)
    const end = Math.min(normalizedTotal, start + 4)
    const normalizedStart = Math.max(1, end - 4)
    const pages = []
    for (let page = normalizedStart; page <= end; page += 1) {
      pages.push(page)
    }
    return pages
  }

  function availabilityStatusLabel(book) {
    const statuses = String(book.copy_statuses || '').trim()
    if (statuses) return statuses
    return book.status || ((book.available_copies || 0) > 0 ? 'available' : 'unavailable')
  }

  function renderPage() {
    if (activePage === 'overview') {
      const requestRate = Math.min(100, Math.round((pendingBorrowRequests.length / Math.max(1, safeBorrowRequests.length || 1)) * 100))
      const overdueRate = Math.min(100, Math.round((overdueLoans.length / Math.max(1, activeLoans.length || 1)) * 100))
      const recentTransactions = safeLoans
        .slice()
        .sort((a, b) => new Date(b.return_date || b.borrow_date || b.issue_date || 0) - new Date(a.return_date || a.borrow_date || a.issue_date || 0))
        .slice(0, 5)
      const reservationPreview = safeReservations
        .slice()
        .sort((a, b) => new Date(b.reservation_date || 0) - new Date(a.reservation_date || 0))
        .slice(0, 4)

      return (
        <div className="dashboard-shell">
          <section className="dashboard-hero">
            <div>
              <div className="eyebrow"><Sparkles size={14} aria-hidden="true" /> Live circulation desk</div>
              <h2>Library Operations Overview</h2>
              <p>Track requests, loans, reservations, overdue activity, and fine reviews from one focused workspace.</p>
            </div>
            <div className="hero-actions">
              <button className="dash-action primary" type="button" onClick={() => setActivePage('issue-return')}>Review Requests <ArrowUpRight size={16} aria-hidden="true" /></button>
              <button className="dash-action" type="button" onClick={() => setActivePage('returns')}>Process Return</button>
            </div>
          </section>

          <section className="metric-grid">
            {stats.map((stat) => (
              <div key={stat.label} className={`metric-card ${stat.type}`}>
                <div className="metric-top">
                  <span>{stat.label}</span>
                  <stat.icon size={20} strokeWidth={1.9} aria-hidden="true" />
                </div>
                <div className="metric-value">{stat.value}</div>
                <div className="metric-foot">Updated with current records</div>
              </div>
            ))}
          </section>

          <section className="dashboard-grid">
            <div className="insight-card wide">
              <div className="insight-header">
                <div>
                  <div className="card-title">Circulation Analytics</div>
                  <div className="subtext">A quick read on workload and service pressure.</div>
                </div>
                <Activity size={20} aria-hidden="true" />
              </div>
              <div className="analytics-bars">
                <div className="analytics-row">
                  <div><span>Pending request load</span><strong>{pendingBorrowRequests.length} open</strong></div>
                  <div className="progress-track"><div className="progress-fill gold" style={{ width: `${requestRate}%` }} /></div>
                </div>
                <div className="analytics-row">
                  <div><span>Overdue pressure</span><strong>{overdueLoans.length} of {activeLoans.length} active loans</strong></div>
                  <div className="progress-track"><div className="progress-fill red" style={{ width: `${overdueRate}%` }} /></div>
                </div>
                <div className="analytics-row">
                  <div><span>Reservation queue</span><strong>{activeReservationCount} active or ready</strong></div>
                  <div className="progress-track"><div className="progress-fill blue" style={{ width: `${Math.min(100, activeReservationCount * 18)}%` }} /></div>
                </div>
              </div>
            </div>

            <div className="insight-card">
              <div className="insight-header">
                <div>
                  <div className="card-title">Quick Actions</div>
                  <div className="subtext">Common circulation tasks.</div>
                </div>
                <Zap size={20} aria-hidden="true" />
              </div>
              <div className="quick-grid">
                <button className="quick-tile gold" type="button" onClick={() => setActivePage('issue-return')}><BookOpen size={18} /> Review Requests</button>
                <button className="quick-tile" type="button" onClick={() => setActivePage('overdue')}><Clock3 size={18} /> View Overdue</button>
                <button className="quick-tile" type="button" onClick={() => setActivePage('students')}><Users size={18} /> Student Records</button>
                <button className="quick-tile" type="button" onClick={() => setActivePage('availability')}><Search size={18} /> Availability</button>
              </div>
            </div>

            <div className="insight-card">
              <div className="insight-header"><div><div className="card-title">Latest Borrow / Return</div><div className="subtext">Recent circulation records.</div></div></div>
              <div className="activity-list">
                {recentTransactions.length === 0 ? (
                  <div className="empty-state">No circulation records yet.</div>
                ) : recentTransactions.map((loan) => (
                  <div className="activity-item" key={loan.loan_id || loan.borrow_id}>
                    <div className={`activity-dot ${loan.returned || loan.return_date ? 'green' : isLoanOverdue(loan) ? 'red' : 'gold'}`} />
                    <div>
                      <strong>{loan.book_title || loan.book_id || 'Unknown book'}</strong>
                      <span>{loan.student_name || loan.student_email || `Student ${loan.student_id || ''}`}</span>
                    </div>
                    <em>{loan.returned || loan.return_date ? 'Returned' : isLoanOverdue(loan) ? 'Overdue' : 'Borrowed'}</em>
                  </div>
                ))}
              </div>
            </div>

            <div className="insight-card">
              <div className="insight-header"><div><div className="card-title">Reservation Summary</div><div className="subtext">Latest queue movement.</div></div></div>
              <div className="activity-list">
                {reservationPreview.length === 0 ? (
                  <div className="empty-state">No active reservations.</div>
                ) : reservationPreview.map((reservation) => (
                  <div className="activity-item" key={reservation.reservation_id}>
                    <div className="activity-dot blue" />
                    <div>
                      <strong>{reservation.book_title || reservation.book_id}</strong>
                      <span>Queue #{reservation.queue_position || '-'} - {reservation.status || 'active'}</span>
                    </div>
                    <em>{reservation.expiration_date ? formatDate(reservation.expiration_date) : 'Open'}</em>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>
      )
    }

    if (activePage === 'issue-return') {
      return (
        <>
          <div className="card">
            <div className="card-hdr"><div className="card-title">Pending Borrow Requests ({pendingBorrowRequests.length})</div></div>
            <div className="admin-table-container">
              <table>
                <thead>
                  <tr><th>Request</th><th>Student</th><th>Book</th><th>Requested</th><th>Due Date</th><th>Action</th></tr>
                </thead>
                <tbody>
                  {pendingBorrowRequests.length === 0 ? (
                    <tr><td colSpan="6" style={{ color: 'var(--muted)', textAlign: 'center', padding: '18px' }}>No pending borrow requests.</td></tr>
                  ) : (
                    pendingBorrowRequests.map((request) => (
                      <tr key={request.request_id}>
                        <td>{request.request_id}</td>
                        <td>{request.student_name || request.student_number || request.student_id}</td>
                        <td>{request.book_title || request.book_id}</td>
                        <td>{request.requested_at ? new Date(request.requested_at).toLocaleString() : ''}</td>
                        <td>
                          <input
                            className="table-date-input"
                            type="date"
                            value={requestDueDates[request.request_id] || ''}
                            onChange={(event) => setRequestDueDates({ ...requestDueDates, [request.request_id]: event.target.value })}
                          />
                        </td>
                        <td>
                          <div className="row-actions">
                            <button className="btn btn-green btn-sm" type="button" onClick={() => handleApproveRequest(request.request_id)}>Approve</button>
                            <button className="btn btn-outline btn-sm" type="button" onClick={() => handleRejectRequest(request.request_id)}>Reject</button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
          <div className="card">
            <div className="card-hdr"><div className="card-title">Barcode / QR Scanner</div></div>
            <form className="admin-form scan-form" onSubmit={handleLookupScan}>
              <div className="frow scan-grid">
                <div className="fgroup">
                  <label>Barcode or QR value</label>
                  <input value={scanForm.code} onChange={(event) => setScanForm({ ...scanForm, code: event.target.value })} placeholder="Scan or paste code" autoComplete="off" />
                </div>
                <div className="fgroup">
                  <label>Student ID</label>
                  <input value={scanForm.student_id} onChange={(event) => setScanForm({ ...scanForm, student_id: event.target.value })} placeholder="Required for issue" />
                </div>
              </div>
              <div className="scan-actions">
                <button className="btn btn-outline" type="submit">Lookup</button>
                <button className="btn btn-blue" type="button" onClick={handleIssueByScan}>Issue</button>
              </div>
            </form>
            {scanResult && (
              <div className="scan-result">
                <strong>{scanResult.book_title}</strong>
                <span>{scanResult.copy_code} / {scanResult.status}</span>
              </div>
            )}
          </div>
        </>
      )
    }

    if (activePage === 'returns') {
      return (
        <ReturnPlatform onLoanReturned={async () => {
          await Promise.allSettled([loadBorrowRequests(), loadLoans(), loadBooks(), loadAvailabilityBooks(), loadReservations()])
        }} />
      )
    }

    if (activePage === 'availability') {
      const currentPage = availabilityPagination.page || 1
      const totalPages = Math.max(1, availabilityPagination.total_pages || 1)
      const totalRecords = availabilityPagination.total || 0
      return (
        <div className="card">
          <div className="card-hdr">
            <div className="card-title">Book Availability</div>
            <div className="availability-count">{totalRecords} records</div>
          </div>
          <div className="availability-filters">
            <div className="fgroup">
              <label>Title</label>
              <input value={availabilityFilters.title} onChange={(event) => updateAvailabilityFilter('title', event.target.value)} placeholder="Search title" />
            </div>
            <div className="fgroup">
              <label>ISBN</label>
              <input value={availabilityFilters.isbn} onChange={(event) => updateAvailabilityFilter('isbn', event.target.value)} placeholder="Search ISBN" />
            </div>
            <div className="fgroup">
              <label>Status</label>
              <select value={availabilityFilters.availability} onChange={(event) => updateAvailabilityFilter('availability', event.target.value)}>
                <option value="">All</option>
                <option value="available">Available</option>
                <option value="borrowed">Borrowed</option>
                <option value="reserved">Reserved</option>
                <option value="lost">Lost</option>
                <option value="maintenance">Maintenance</option>
              </select>
            </div>
            <div className="fgroup">
              <label>Per page</label>
              <select value={availabilityPagination.limit} onChange={(event) => setAvailabilityPagination(prev => ({ ...prev, page: 1, limit: Number(event.target.value) }))}>
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
              </select>
            </div>
          </div>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr><th>Title</th><th>ISBN</th><th>Available</th><th>Total</th><th>Status</th><th>Copies</th></tr>
              </thead>
              <tbody>
                {availabilityLoading ? (
                  <tr><td colSpan="7">Loading availability...</td></tr>
                ) : safeAvailabilityBooks.length === 0 ? (
                  <tr><td colSpan="7">No books match the current filters.</td></tr>
                ) : safeAvailabilityBooks.map((book) => (
                  <tr key={book.book_id}>
                    <td>{book.title}</td>
                    <td>{book.isbn || '—'}</td>
                    <td>{book.available_copies || 0}</td>
                    <td>{book.total_copies || 0}</td>
                    <td>{availabilityStatusLabel(book)}</td>
                    <td>{book.copy_count || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pagination-bar">
            <button className="btn btn-outline btn-sm" type="button" disabled={currentPage <= 1 || availabilityLoading} onClick={() => setAvailabilityPage(currentPage - 1)}>Previous</button>
            <div className="page-buttons">
              {availabilityPageNumbers().map((page) => (
                <button
                  key={page}
                  className={`page-button ${page === currentPage ? 'active' : ''}`}
                  type="button"
                  disabled={availabilityLoading}
                  onClick={() => setAvailabilityPage(page)}
                >
                  {page}
                </button>
              ))}
            </div>
            <button className="btn btn-outline btn-sm" type="button" disabled={currentPage >= totalPages || availabilityLoading} onClick={() => setAvailabilityPage(currentPage + 1)}>Next</button>
            <span className="pagination-summary">Page {currentPage} of {totalPages}</span>
          </div>
        </div>
      )
    }

    if (activePage === 'overdue') {
      return (
        <div className="card">
          <div className="card-hdr">
            <div className="card-title">Overdue Books ({overdueLoans.length})</div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button className="btn btn-outline btn-sm" type="button" onClick={() => handleSendReminders('due')}>Due Soon</button>
              <button className="btn btn-gold btn-sm" type="button" onClick={() => handleSendReminders('overdue')}>Overdue Email</button>
            </div>
          </div>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr><th>Loan ID</th><th>Book</th><th>Copy</th><th>Student</th><th>Due Date</th><th>Days Overdue</th></tr>
              </thead>
              <tbody>
                {overdueLoans.length === 0 ? (
                  <tr><td colSpan="6" className="empty-cell">No overdue loans.</td></tr>
                ) : (
                  overdueLoans.map((loan) => {
                    const daysOverdue = Math.max(0, Number(loan.days_overdue || Math.floor((new Date() - new Date(loan.due_date)) / (1000 * 60 * 60 * 24))))
                    return (
                      <tr key={loan.loan_id}>
                        <td>{loan.loan_id}</td>
                        <td>{loan.book_title || loan.book_id}</td>
                        <td>{loan.copy_code || loan.barcode_value || '-'}</td>
                        <td>{loan.student_name || loan.user_id}</td>
                        <td>{formatLoanDate(loan.due_date)}</td>
                        <td style={{ color: 'var(--red)', fontWeight: 'bold' }}>{daysOverdue} days</td>
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
          <div className="card-hdr">
            <div className="card-title">Reservation Queue ({safeReservations.length})</div>
            <button className="btn btn-outline btn-sm" type="button" onClick={handleExpireReservations}>Remove Expired</button>
          </div>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr><th>Book</th><th>Student</th><th>Queue</th><th>Status</th><th>Expires</th><th>Copy</th><th>Action</th></tr>
              </thead>
              <tbody>
                {safeReservations.length === 0 ? (
                  <tr><td colSpan="7" className="empty-cell">No reservations found.</td></tr>
                ) : (
                  safeReservations.map((reservation) => {
                    const status = String(reservation.status || '').toLowerCase()
                    const busy = reservationActionId === reservation.reservation_id
                    return (
                      <tr key={reservation.reservation_id}>
                        <td>{reservation.book_title || reservation.book_id}</td>
                        <td>{reservation.student_name || reservation.student_email || reservation.student_id}</td>
                        <td>{reservation.queue_position || '-'}</td>
                        <td style={{ color: status === 'ready' ? 'var(--green)' : status === 'active' ? 'var(--gold)' : 'var(--muted)' }}>{statusLabel(status)}</td>
                        <td>{formatLoanDate(reservation.expiration_date)}</td>
                        <td>{reservation.copy_code || reservation.barcode_value || '-'}</td>
                        <td>
                          <div className="table-actions">
                            {status === 'active' && (
                              <button className="btn btn-blue btn-sm" type="button" disabled={busy} onClick={() => handleReservationAction(reservation.reservation_id, 'approve')}>
                                Approve
                              </button>
                            )}
                            {status === 'ready' && (
                              <button className="btn btn-green btn-sm" type="button" disabled={busy} onClick={() => handleReservationAction(reservation.reservation_id, 'claim')}>
                                Claim
                              </button>
                            )}
                            {['active', 'ready'].includes(status) ? (
                              <button className="btn btn-outline btn-sm" type="button" disabled={busy} onClick={() => handleReservationAction(reservation.reservation_id, 'cancel')}>
                                Cancel
                              </button>
                            ) : (
                              <span style={{ color: 'var(--muted)' }}>Closed</span>
                            )}
                          </div>
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

    if (activePage === 'students') {
      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">Student Records</div></div>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr><th>Student ID</th><th>Name</th><th>Email</th><th>Status</th><th>Books Borrowed</th></tr>
              </thead>
              <tbody>
                {studentList.map((student) => {
                  const borrowedCount = safeLoans.filter(l => l.user_id === student.user_id && !l.returned).length
                  return (
                    <tr key={student.user_id}>
                      <td>{student.user_id}</td>
                      <td>{student.full_name || student.name}</td>
                      <td>{student.email}</td>
                      <td>{student.status || 'Active'}</td>
                      <td>{borrowedCount}</td>
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
      const realEbooks = safeEbooks.filter(e => !e.is_catalog_only)
      const totalPages = Math.max(1, Math.ceil(realEbooks.length / ebookLibraryPageSize))
      const currentPage = Math.min(Math.max(1, ebookPage || 1), totalPages)
      const firstResult = realEbooks.length === 0 ? 0 : ((currentPage - 1) * ebookLibraryPageSize) + 1
      const lastResult = Math.min(currentPage * ebookLibraryPageSize, realEbooks.length)
      const visibleEbooks = realEbooks.slice((currentPage - 1) * ebookLibraryPageSize, currentPage * ebookLibraryPageSize)

      return (
        <div className="card">
          <div className="card-hdr">
            <div className="card-title">E-book Library</div>
            <div className="availability-count">
              {realEbooks.length > 0 ? `${firstResult}-${lastResult} of ${realEbooks.length} records` : '0 records'}
            </div>
          </div>
          <div className="ebook-upload-form">
            <div className="ebook-upload-grid">
              <div className="fgroup">
                <label htmlFor="ebook-title">E-BOOK TITLE</label>
                <input
                  id="ebook-title"
                  type="text"
                  value={ebookUploadTitle}
                  onChange={(event) => setEbookUploadTitle(event.target.value)}
                  placeholder="Optional display title"
                />
              </div>

              <div className="fgroup">
                <label htmlFor="ebook-file">PDF / EPUB</label>
                <input
                  id="ebook-file"
                  type="file"
                  accept=".pdf,.epub"
                  onChange={(event) => setEbookUploadFile(event.target.files?.[0] || null)}
                />
              </div>
              <div className="ebook-upload-actions">
                <button
                  className="btn btn-blue"
                  type="button"
                  disabled={ebookUploading}
                  onClick={handleUploadEbook}
                >
                  {ebookUploading ? 'Uploading...' : 'Upload E-book'}
                </button>
              </div>
            </div>
            {(ebookUploadFile || ebookUploadTitle) && (
              <div className="ebook-upload-summary">
                <strong>Selected file:</strong> {ebookUploadFile?.name || 'None'}
                <strong>Display title:</strong> {ebookUploadTitle || 'Not set'}
              </div>
            )}
          </div>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr><th>Title</th><th>Book</th><th>Type</th><th>Size</th><th>Access</th></tr>
              </thead>
              <tbody>
                {ebookLoading ? (
                  <tr><td colSpan="5" className="empty-cell">Loading e-books...</td></tr>
                ) : visibleEbooks.length === 0 ? (
                  <tr><td colSpan="5" className="empty-cell">No e-books available yet.</td></tr>
                ) : visibleEbooks.map((ebook) => (
                  <tr key={ebook.ebook_id}>
                    <td>
                      <div className="ebook-title-cell">
                        <strong>{ebook.title}</strong>
                        {ebook.original_filename && <span>{ebook.original_filename}</span>}
                      </div>
                    </td>
                    <td>{ebook.book_title || ebook.title}</td>
                    <td>
                      <span className={`file-type-badge ${String(ebook.file_type || '').toLowerCase()}`}>
                        {String(ebook.file_type || '').toUpperCase()}
                      </span>
                    </td>
                    <td>{`${Math.ceil((ebook.file_size || 0) / 1024)} KB`}</td>
                    <td>
                      <div className="table-actions">
                        <a className="btn btn-outline btn-sm" href={`/ebooks/${ebook.ebook_id}`} target="_blank" rel="noreferrer">Open</a>
                        {ebook.file_available === false && (
                          <span style={{ color: 'var(--error)', fontSize: '12px', marginRight: '8px' }}>File missing</span>
                        )}
                        <button className="btn btn-blue btn-sm" type="button" disabled={ebook.file_available === false} onClick={() => handleDownloadEbook(ebook)}>Download</button>
                        <button className="btn btn-red btn-sm" type="button" onClick={() => handleDeleteEbook(ebook)} style={{ marginLeft: '8px' }}>Delete</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {realEbooks.length > ebookLibraryPageSize && (
            <div className="pagination-bar">
              <button className="btn btn-outline btn-sm" type="button" disabled={currentPage <= 1 || ebookLoading} onClick={() => setEbookLibraryPage(currentPage - 1)}>Previous</button>
              <div className="page-buttons">
                {ebookPageNumbers().map((page) => (
                  <button
                    key={page}
                    className={`page-button ${page === currentPage ? 'active' : ''}`}
                    type="button"
                    disabled={ebookLoading}
                    onClick={() => setEbookLibraryPage(page)}
                  >
                    {page}
                  </button>
                ))}
              </div>
              <button className="btn btn-outline btn-sm" type="button" disabled={currentPage >= totalPages || ebookLoading} onClick={() => setEbookLibraryPage(currentPage + 1)}>Next</button>
              <span className="pagination-summary">Page {currentPage} of {totalPages}</span>
            </div>
          )}
        </div>
      )
    }

    if (activePage === 'search') {
      const filtered = safeBooks.filter(b =>
        b.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (b.author && b.author.toLowerCase().includes(searchQuery.toLowerCase()))
      )
      const totalPages = Math.max(1, Math.ceil(filtered.length / bookSearchPageSize))
      const currentPage = Math.min(Math.max(1, bookSearchPage || 1), totalPages)
      const firstResult = filtered.length === 0 ? 0 : ((currentPage - 1) * bookSearchPageSize) + 1
      const lastResult = Math.min(currentPage * bookSearchPageSize, filtered.length)
      const visibleBooks = filtered.slice((currentPage - 1) * bookSearchPageSize, currentPage * bookSearchPageSize)
      return (
        <div className="card">
          <div className="card-hdr">
            <div className="card-title">Search Books</div>
            <div className="availability-count">
              {filtered.length > 0 ? `${firstResult}-${lastResult} of ${filtered.length} records` : '0 records'}
            </div>
          </div>
          <div style={{ marginBottom: '20px' }}>
            <input
              className="search-input"
              value={searchQuery}
              onChange={(event) => {
                setSearchQuery(event.target.value)
                setBookSearchPage(1)
              }}
              placeholder="Search by title or author..."
            />
          </div>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr><th>Title</th><th>Author</th><th>ISBN</th><th>Available</th></tr>
              </thead>
              <tbody>
                {visibleBooks.length === 0 ? (
                  <tr><td colSpan="4" className="empty-cell">No books match the current search.</td></tr>
                ) : visibleBooks.map((book) => (
                  <tr key={book.book_id}>
                    <td>{book.title}</td>
                    <td>{book.author || '—'}</td>
                    <td>{book.isbn || '—'}</td>
                    <td>{(book.available_copies || 0) > 0 ? 'Yes' : 'No'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {totalPages > 1 && (
            <div className="pagination-bar">
              <button className="btn btn-outline btn-sm" type="button" disabled={currentPage <= 1} onClick={() => setSearchBookPage(currentPage - 1, totalPages)}>Previous</button>
              <div className="page-buttons">
                {searchBookPageNumbers(totalPages, currentPage).map((page) => (
                  <button
                    key={page}
                    className={`page-button ${page === currentPage ? 'active' : ''}`}
                    type="button"
                    onClick={() => setSearchBookPage(page, totalPages)}
                  >
                    {page}
                  </button>
                ))}
              </div>
              <button className="btn btn-outline btn-sm" type="button" disabled={currentPage >= totalPages} onClick={() => setSearchBookPage(currentPage + 1, totalPages)}>Next</button>
              <span className="pagination-summary">Page {currentPage} of {totalPages}</span>
            </div>
          )}
        </div>
      )
    }

    if (activePage === 'fines') {
      const paymentStatusLabel = (fine) => {
        const paymentStatus = String(fine.payment_status || '').toLowerCase()
        if (paymentStatus === 'pending') return 'Cash Pending'
        if (paymentStatus === 'pending_verification') return 'Pending Verification'
        if (paymentStatus === 'failed') return 'Rejected'
        if (paymentStatus === 'paid') return 'Paid'
        return fine.status === 'paid' ? 'Paid' : 'Unpaid'
      }

      return (
        <>
          <div className="grid4">
            <div className="stat red">
              <div className="stat-label">Unpaid</div>
              <div className="stat-num">{fineSummary.unpaid_count || 0}</div>
              <div className="stat-sub">{formatCurrency(fineSummary.total_unpaid)}</div>
            </div>
            <div className="stat gold">
              <div className="stat-label">Pending Review</div>
              <div className="stat-num">{fineSummary.pending_count || pendingFinePayments.length}</div>
              <div className="stat-sub">Cash or online</div>
            </div>
            <div className="stat green">
              <div className="stat-label">Paid</div>
              <div className="stat-num">{fineSummary.paid_count || 0}</div>
              <div className="stat-sub">{formatCurrency(fineSummary.total_paid)}</div>
            </div>
            <div className="stat blue">
              <div className="stat-label">Total</div>
              <div className="stat-num">{fineSummary.total_count || safeFines.length}</div>
              <div className="stat-sub">Fine records</div>
            </div>
          </div>

          <div className="card">
            <div className="card-hdr">
              <div>
                <div className="card-title">Fine Payment Reviews ({safeFines.length})</div>
                <div className="subtext">View fine payment records. Admin approval is required for payment verification.</div>
              </div>
              <button className="btn btn-outline btn-sm" type="button" disabled={loadingFines} onClick={() => loadFines()}>
                {loadingFines ? 'Refreshing...' : 'Refresh'}
              </button>
            </div>
            <div className="admin-table-container">
              <table>
                <thead>
                  <tr>
                    <th>Fine ID</th>
                    <th>Student</th>
                    <th>Book</th>
                    <th>Amount</th>
                    <th>Payment</th>
                    <th>Reference</th>
                    <th>Review</th>
                  </tr>
                </thead>
                <tbody>
                  {safeFines.length === 0 ? (
                    <tr><td colSpan="7" className="empty-cell">No fines found.</td></tr>
                  ) : safeFines.map((fine) => {
                    const paymentStatus = String(fine.payment_status || '').toLowerCase()
                    const isPendingReview = ['pending', 'pending_verification'].includes(paymentStatus)
                    return (
                      <tr key={fine.fine_id}>
                        <td>{fine.fine_id}</td>
                        <td>
                          <strong>{fine.student_name || 'Unknown student'}</strong>
                          <div className="muted-line">{fine.student_number || fine.student_email || `Student ${fine.student_id}`}</div>
                        </td>
                        <td>{fine.book_title || fine.book_id || 'Unknown book'}</td>
                        <td>{formatCurrency(fine.amount)}</td>
                        <td>
                          <span className={`fine-pill ${paymentStatus || 'unpaid'}`}>{paymentStatusLabel(fine)}</span>
                          {fine.payment_method && <div className="muted-line">{fine.payment_method}</div>}
                        </td>
                        <td>
                          {fine.payment_reference || '-'}
                          {fine.payment_requested_at && <div className="muted-line">{new Date(fine.payment_requested_at).toLocaleString()}</div>}
                        </td>
                        <td>
                          <span className="muted-line">{isPendingReview ? 'Waiting for admin' : 'View only'}</span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )
    }

    return null
  }

  return (
    <div className="librarian-dashboard-app">
      <button className="mobile-menu-button" type="button" onClick={() => setMobileNavOpen(true)} aria-label="Open navigation" aria-expanded={mobileNavOpen}>
        <Menu size={20} aria-hidden="true" />
      </button>
      {mobileNavOpen && <button className="mobile-nav-backdrop" type="button" onClick={() => setMobileNavOpen(false)} aria-label="Close navigation" />}
      <div className={`sidebar ${mobileNavOpen ? 'mobile-open' : ''}`}>
        <div className="logo">
          <div className="logo-icon"><BookOpen size={24} strokeWidth={1.9} aria-hidden="true" /></div>
          <div className="logo-text">
            <div className="logo-title">LIBRASYS</div>
            <div className="logo-sub">Librarian</div>
          </div>
          <button className="mobile-sidebar-close" type="button" onClick={() => setMobileNavOpen(false)} aria-label="Close navigation">
            <X size={18} aria-hidden="true" />
          </button>
        </div>
        <nav className="nav">
          {navigationSections.map((section) => (
            <div key={section.section}>
              <div className="nav-section">{section.section}</div>
              {section.items.map((item) => (
                <div key={item.id} className={`nav-item ${activePage === item.id ? 'active' : ''}`} onClick={() => handleNavSelect(item.id)}>
                  <span className="nav-icon"><item.icon size={16} strokeWidth={1.8} aria-hidden="true" /></span>
                  <span>{item.title}</span>
                  {item.badge && <span className="nav-badge">{item.badge}</span>}
                </div>
              ))}
            </div>
          ))}
        </nav>
      </div>
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
          <div className="page-title">{pageTitles[activePage] || (activePage === 'ebooks' ? 'E-books' : 'Overview')}</div>
          <div style={{ position: 'relative' }}>
            <button type="button" className="icon-button notification-button" onClick={() => setShowNotifications(!showNotifications)} aria-label="Notifications">
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
                        <button onClick={() => removeNotification(notif.id)} style={{ background: 'none', border: 'none', color: 'var(--muted)', cursor: 'pointer', fontSize: '12px' }}>✕</button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
          <div className="topbar-user-card">
            <div
              className="topbar-user-profile"
              role="button"
              tabIndex={0}
              onClick={() => openAccountModal('profile')}
              onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); openAccountModal('profile') } }}
              aria-label="Open account settings"
            >
              <div className="avatar">LI</div>
              <div className="topbar-user-text">
                <div className="topbar-user-name">Librarian</div>
                <div className="topbar-user-email">librarian@librasys.edu</div>
              </div>
            </div>
            <button className="topbar-logout-button" type="button" title="Logout" onClick={() => setShowLogoutConfirm(true)} aria-label="Logout">
              <Power size={17} aria-hidden="true" />
            </button>
          </div>
        </div>

        {showAccountModal && (
          <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="account-modal-title">
            <div className="modal" role="document">
              <div className="modal-header">
                <div id="account-modal-title" className="modal-title">Account Settings</div>
              </div>
              <div className="modal-body">
                <div className="tabs">
                  <button type="button" className={accountTab === 'profile' ? 'tab active' : 'tab'} onClick={() => setAccountTab('profile')}>
                    Profile
                  </button>
                  <button type="button" className={accountTab === 'security' ? 'tab active' : 'tab'} onClick={() => setAccountTab('security')}>
                    Security
                  </button>
                </div>
                {accountTab === 'profile' ? (
                  <div className="account-details">
                    <div className="fgroup">
                      <label>Email</label>
                      <input type="text" value="librarian@librasys.edu" readOnly />
                    </div>
                    <div className="fgroup">
                      <label>Role</label>
                      <input type="text" value="Librarian" readOnly />
                    </div>
                  </div>
                ) : (
                  <PasswordChangeForm
                    form={passwordForm}
                    onFieldChange={updatePasswordField}
                    onSubmit={handleChangePassword}
                    error={passwordError}
                    success={passwordSuccess}
                    submitting={passwordSaving}
                  />
                )}
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-close" onClick={() => setShowAccountModal(false)}>
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="content">
          {renderPage()}
        </div>
      </div>
    </div>
  )
}
