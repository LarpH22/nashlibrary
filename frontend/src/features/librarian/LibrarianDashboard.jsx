import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../shared/api.js'
import { clearStoredAuth } from '../../shared/authStorage.js'
import './LibrarianDashboard.css'

const baseNavSections = [
  {
    section: 'MAIN',
    items: [
      { id: 'overview', icon: '📊', title: 'Overview' },
      { id: 'issue-return', icon: '📖', title: 'Borrow Approvals' },
      { id: 'availability', icon: '🔍', title: 'Book Availability' },
      { id: 'overdue', icon: '⏰', title: 'Overdue Books' }
    ]
  },
  {
    section: 'RECORDS',
    items: [
      { id: 'students', icon: '👥', title: 'Student Records' },
      { id: 'search', icon: '🔎', title: 'Search Books' }
    ]
  },
  {
    section: 'ACCOUNT',
    items: [
      { id: 'account', icon: '🔑', title: 'Change Password' }
    ]
  }
]

const pageTitles = {
  overview: 'Overview',
  'issue-return': 'Borrow Approvals',
  availability: 'Book Availability',
  overdue: 'Overdue Books',
  students: 'Student Records',
  search: 'Search Books',
  account: 'Change Password'
}

const ebookCatalogPageSize = 100
const ebookLibraryPageSize = 10

async function fetchAllCatalogBooks() {
  const firstPage = await api.get('/api/books/search', { params: { page: 1, limit: ebookCatalogPageSize } })
  const books = Array.isArray(firstPage.data?.books) ? [...firstPage.data.books] : []
  const totalPages = Number(firstPage.data?.pagination?.total_pages || 1)

  for (let page = 2; page <= totalPages; page += 1) {
    const response = await api.get('/api/books/search', { params: { page, limit: ebookCatalogPageSize } })
    if (Array.isArray(response.data?.books)) {
      books.push(...response.data.books)
    }
  }

  return books
}

function mergeEbooksWithCatalog(ebookRows, catalogBooks) {
  const rows = Array.isArray(ebookRows) ? [...ebookRows] : []
  const ebookBookIds = new Set(rows.map((ebook) => Number(ebook.book_id)).filter(Boolean))

  for (const book of catalogBooks || []) {
    const bookId = Number(book?.book_id || book?.id)
    if (!bookId || ebookBookIds.has(bookId)) {
      continue
    }

    rows.push({
      ebook_id: `book-${bookId}`,
      book_id: bookId,
      title: book.title,
      book_title: book.title,
      file_type: 'book',
      file_size: null,
      is_catalog_only: true
    })
  }

  return rows
}

const isLoanReturned = (loan) => loan.returned || String(loan.status || '').toLowerCase() === 'returned'

const isLoanOverdue = (loan) => {
  if (isLoanReturned(loan) || !loan.due_date) {
    return false
  }

  const dueDate = new Date(loan.due_date)
  return !Number.isNaN(dueDate.getTime()) && dueDate < new Date()
}

export function LibrarianDashboard() {
  const navigate = useNavigate()
  const [activePage, setActivePage] = useState('overview')
  const [books, setBooks] = useState([])
  const [ebooks, setEbooks] = useState([])
  const [ebookPage, setEbookPage] = useState(1)
  const [ebookLoading, setEbookLoading] = useState(false)
  const [availabilityBooks, setAvailabilityBooks] = useState([])
  const [availabilityFilters, setAvailabilityFilters] = useState({ title: '', author: '', category: '', isbn: '', availability: '' })
  const [availabilityPagination, setAvailabilityPagination] = useState({ page: 1, limit: 10, total: 0, total_pages: 1 })
  const [availabilityLoading, setAvailabilityLoading] = useState(false)
  const [loans, setLoans] = useState([])
  const [borrowRequests, setBorrowRequests] = useState([])
  const [students, setStudents] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [requestDueDates, setRequestDueDates] = useState({})
  const [scanForm, setScanForm] = useState({ code: '', student_id: '' })
  const [scanResult, setScanResult] = useState(null)
  const [returnLoanId, setReturnLoanId] = useState('')
  const [passwordForm, setPasswordForm] = useState({ old_password: '', new_password: '' })
  const [notifications, setNotifications] = useState([])
  const [showNotifications, setShowNotifications] = useState(false)
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [passwordError, setPasswordError] = useState('')

  const addNotification = (text) => {
    const id = Date.now()
    setNotifications(prev => [...prev, { id, text, timestamp: new Date() }])
  }

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }

  const safeBooks = useMemo(() => (Array.isArray(books) ? books : []), [books])
  const safeEbooks = useMemo(() => (Array.isArray(ebooks) ? ebooks : []), [ebooks])
  const safeAvailabilityBooks = useMemo(() => (Array.isArray(availabilityBooks) ? availabilityBooks : []), [availabilityBooks])
  const safeLoans = useMemo(() => (Array.isArray(loans) ? loans : []), [loans])
  const safeBorrowRequests = useMemo(() => (Array.isArray(borrowRequests) ? borrowRequests : []), [borrowRequests])
  const safeStudents = useMemo(() => (Array.isArray(students) ? students : []), [students])
  const pendingBorrowRequests = useMemo(() => safeBorrowRequests.filter((request) => request.status === 'pending'), [safeBorrowRequests])
  const overdueLoans = useMemo(() => safeLoans.filter(isLoanOverdue), [safeLoans])
  const navigationSections = useMemo(
    () => baseNavSections.map((section) => {
      const sectionItems = section.section === 'RECORDS'
        ? [
            ...section.items.filter((item) => item.id !== 'search'),
            { id: 'ebooks', icon: 'EB', title: 'E-books' },
            ...section.items.filter((item) => item.id === 'search')
          ]
        : section.items

      return {
        ...section,
        items: sectionItems.map((item) => (
          item.id === 'overdue'
            ? { ...item, badge: overdueLoans.length > 0 ? String(overdueLoans.length) : '' }
            : item
        ))
      }
    }),
    [overdueLoans.length]
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
      const [ebookResponse, catalogBooks] = await Promise.all([
        api.get('/books/ebooks'),
        fetchAllCatalogBooks()
      ])
      setEbooks(mergeEbooksWithCatalog(ebookResponse.data?.ebooks, catalogBooks))
    } catch (error) {
      console.error('Unable to load e-books:', error)
      setEbooks([])
      addNotification('Unable to load e-books.')
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
          author: availabilityFilters.author.trim(),
          category: availabilityFilters.category.trim(),
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

  useEffect(() => {
    loadBooks()
    loadEbooks()
    loadLoans()
    loadBorrowRequests()
    loadStudents()
  }, [loadBooks, loadEbooks, loadLoans, loadBorrowRequests, loadStudents])

  useEffect(() => {
    loadAvailabilityBooks()
  }, [loadAvailabilityBooks])

  useEffect(() => {
    const totalPages = Math.max(1, Math.ceil(safeEbooks.length / ebookLibraryPageSize))
    setEbookPage((currentPage) => Math.min(currentPage, totalPages))
  }, [safeEbooks.length])

  const stats = useMemo(
    () => [
      { label: 'Books', value: safeBooks.length, type: 'blue' },
      { label: 'Pending Requests', value: pendingBorrowRequests.length, type: 'gold' },
      { label: 'Active Loans', value: safeLoans.filter(l => !isLoanReturned(l)).length, type: 'green' },
      { label: 'Overdue', value: overdueLoans.length, type: 'red' },
      { label: 'Students', value: studentList.length, type: 'purple' }
    ],
    [safeBooks, pendingBorrowRequests, safeLoans, overdueLoans.length, studentList]
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
      await Promise.allSettled([loadBorrowRequests(), loadLoans(), loadBooks(), loadAvailabilityBooks()])
      addNotification('Borrow request approved.')
    } catch (error) {
      console.error('Error approving request:', error)
      await Promise.allSettled([loadBorrowRequests(), loadLoans(), loadBooks(), loadAvailabilityBooks()])
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

  async function handleReturnBook(event) {
    event.preventDefault()
    const loanId = Number(returnLoanId)
    if (!returnLoanId || Number.isNaN(loanId) || loanId <= 0) {
      addNotification('Please enter a valid Loan ID before returning a book.')
      return
    }

    try {
      await api.post('/books/return', { loan_id: loanId })
      setReturnLoanId('')
      await Promise.allSettled([loadBorrowRequests(), loadLoans(), loadBooks(), loadAvailabilityBooks()])
      addNotification('Book return recorded.')
    } catch (error) {
      console.error('Error returning book:', error)
      await Promise.allSettled([loadLoans(), loadBooks(), loadAvailabilityBooks()])
      addNotification(error?.response?.data?.message || 'Failed to return book.')
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
      await Promise.allSettled([loadLoans(), loadBooks(), loadAvailabilityBooks()])
      addNotification('Book issued from scan.')
    } catch (error) {
      await Promise.allSettled([loadLoans(), loadBooks(), loadAvailabilityBooks()])
      addNotification(error?.response?.data?.message || 'Failed to issue scanned copy.')
    }
  }

  async function handleReturnByScan() {
    if (!scanForm.code.trim()) {
      addNotification('Scan or enter a barcode/QR value first.')
      return
    }
    try {
      await api.post('/books/return-by-scan', { code: scanForm.code.trim() })
      setScanForm({ code: '', student_id: '' })
      setScanResult(null)
      await Promise.allSettled([loadLoans(), loadBooks(), loadAvailabilityBooks()])
      addNotification('Book returned from scan.')
    } catch (error) {
      await Promise.allSettled([loadLoans(), loadBooks(), loadAvailabilityBooks()])
      addNotification(error?.response?.data?.message || 'Failed to return scanned copy.')
    }
  }

  async function handleDownloadEbook(ebook) {
    if (ebook.is_catalog_only) {
      return
    }

    try {
      const response = await api.get(`/books/ebooks/${ebook.ebook_id}/download`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(response.data)
      const link = document.createElement('a')
      link.href = url
      link.download = ebook.original_filename || `${ebook.title}.${ebook.file_type || 'pdf'}`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      addNotification(error?.response?.data?.message || 'Unable to download e-book.')
    }
  }

  async function handleDeleteEbook(ebook) {
    if (!window.confirm(`Delete e-book '${ebook.title}'? This cannot be undone.`)) {
      return
    }

    try {
      await api.delete(`/books/ebooks/${ebook.ebook_id}`)
      addNotification('E-book deleted successfully.')
      await loadEbooks()
    } catch (error) {
      addNotification(error?.response?.data?.message || 'Unable to delete e-book.')
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

    // Validate fields
    if (!passwordForm.old_password || !passwordForm.new_password) {
      setPasswordError('Both password fields are required.')
      return
    }

    if (passwordForm.new_password.length < 6) {
      setPasswordError('New password must be at least 6 characters long.')
      return
    }

    try {
      const response = await api.post('/api/admin/password', passwordForm)
      console.log('Password change response:', response.status, response.data)
      const successMessage = response.data?.message
      if (response.status === 200 && successMessage && successMessage.toLowerCase().includes('updated successfully')) {
        setPasswordForm({ old_password: '', new_password: '' })
        setPasswordError('')
        setShowPasswordModal(true)
      } else {
        const errorMsg = successMessage || 'Password change failed. Please try again.'
        console.warn('Password change did not succeed:', response.status, response.data)
        setPasswordError(errorMsg)
      }
    } catch (error) {
      console.error('Error changing password:', error.response?.status, error.response?.data)
      const errorMsg = error.response?.data?.message || error.message || 'Password change failed. Please try again.'
      setPasswordError(errorMsg)
    }
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
    const totalPages = Math.max(1, Math.ceil(safeEbooks.length / ebookLibraryPageSize))
    setEbookPage(Math.min(Math.max(1, page), totalPages))
  }

  function ebookPageNumbers() {
    const totalPages = Math.max(1, Math.ceil(safeEbooks.length / ebookLibraryPageSize))
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

  function availabilityStatusLabel(book) {
    const statuses = String(book.copy_statuses || '').trim()
    if (statuses) return statuses
    return book.status || ((book.available_copies || 0) > 0 ? 'available' : 'unavailable')
  }

  function renderPage() {
    if (activePage === 'overview') {
      return (
        <>
          <div className="grid4">
            {stats.map((stat) => (
              <div key={stat.label} className={`stat ${stat.type}`}>
                <div className="stat-label">{stat.label}</div>
                <div className="stat-num">{stat.value}</div>
                <div className="stat-sub">Current</div>
                <div className="stat-icon">
                  {stat.label === 'Books' ? '📚' : stat.label === 'Active Loans' ? '🔄' : stat.label === 'Overdue' ? '⏰' : '👥'}
                </div>
              </div>
            ))}
          </div>
          <div className="grid2">
            <div className="card">
              <div className="card-hdr"><div className="card-title">Overview</div></div>
              <p>Welcome to the Librarian Dashboard. You can issue and return books, check availability, and manage student records.</p>
            </div>
            <div className="card">
              <div className="card-hdr"><div className="card-title">Quick Actions</div></div>
              <div style={{ display: 'grid', gap: '10px' }}>
                <button className="btn btn-blue" type="button" onClick={() => setActivePage('issue-return')}>Review Requests</button>
                <button className="btn btn-outline" type="button" onClick={() => setActivePage('overdue')}>View Overdue</button>
                <button className="btn btn-outline" type="button" onClick={() => setActivePage('students')}>Student Records</button>
              </div>
            </div>
          </div>
        </>
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
            <div className="card-hdr"><div className="card-title">Return Book</div></div>
            <form className="admin-form" onSubmit={handleReturnBook}>
              <div className="fgroup" style={{ flex: 1 }}>
                <label>Loan ID</label>
                <input value={returnLoanId} onChange={(event) => setReturnLoanId(event.target.value)} placeholder="Loan ID" />
              </div>
              <button className="btn btn-blue" type="submit">Return Book</button>
            </form>
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
                <button className="btn btn-gold" type="button" onClick={handleReturnByScan}>Return</button>
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
              <label>Author</label>
              <input value={availabilityFilters.author} onChange={(event) => updateAvailabilityFilter('author', event.target.value)} placeholder="Search author" />
            </div>
            <div className="fgroup">
              <label>Category</label>
              <input value={availabilityFilters.category} onChange={(event) => updateAvailabilityFilter('category', event.target.value)} placeholder="Search category" />
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
                <tr><th>Loan ID</th><th>Book</th><th>Student</th><th>Due Date</th><th>Days Overdue</th></tr>
              </thead>
              <tbody>
                {overdueLoans.map((loan) => {
                  const daysOverdue = Math.floor((new Date() - new Date(loan.due_date)) / (1000 * 60 * 60 * 24))
                  return (
                    <tr key={loan.loan_id}>
                      <td>{loan.loan_id}</td>
                      <td>{loan.book_title || loan.book_id}</td>
                      <td>{loan.student_name || loan.user_id}</td>
                      <td>{new Date(loan.due_date).toLocaleDateString()}</td>
                      <td style={{ color: 'var(--red)', fontWeight: 'bold' }}>{daysOverdue} days</td>
                    </tr>
                  )
                })}
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
      const totalPages = Math.max(1, Math.ceil(safeEbooks.length / ebookLibraryPageSize))
      const currentPage = Math.min(Math.max(1, ebookPage || 1), totalPages)
      const firstResult = safeEbooks.length === 0 ? 0 : ((currentPage - 1) * ebookLibraryPageSize) + 1
      const lastResult = Math.min(currentPage * ebookLibraryPageSize, safeEbooks.length)
      const visibleEbooks = safeEbooks.slice((currentPage - 1) * ebookLibraryPageSize, currentPage * ebookLibraryPageSize)

      return (
        <div className="card">
          <div className="card-hdr">
            <div className="card-title">E-book Library</div>
            <div className="availability-count">
              {safeEbooks.length > 0 ? `${firstResult}-${lastResult} of ${safeEbooks.length} records` : '0 records'}
            </div>
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
                        {ebook.is_catalog_only ? 'BOOK' : String(ebook.file_type || '').toUpperCase()}
                      </span>
                    </td>
                    <td>{ebook.is_catalog_only ? '-' : `${Math.ceil((ebook.file_size || 0) / 1024)} KB`}</td>
                    <td>
                      <div className="table-actions">
                        <a className="btn btn-outline btn-sm" href={ebook.is_catalog_only ? `/books/${ebook.book_id}` : `/ebooks/${ebook.ebook_id}`} target="_blank" rel="noreferrer">Open</a>
                        {ebook.is_catalog_only ? (
                          <span style={{ color: 'var(--muted)', fontSize: '12px' }}>Catalog only</span>
                        ) : (
                          <>
                            <button className="btn btn-blue btn-sm" type="button" onClick={() => handleDownloadEbook(ebook)}>Download</button>
                            <button className="btn btn-danger btn-sm" type="button" onClick={() => handleDeleteEbook(ebook)} style={{ marginLeft: '8px' }}>Delete</button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {safeEbooks.length > ebookLibraryPageSize && (
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
      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">Search Books</div></div>
          <div style={{ marginBottom: '20px' }}>
            <input
              className="search-input"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search by title or author..."
            />
          </div>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr><th>Title</th><th>Author</th><th>ISBN</th><th>Available</th></tr>
              </thead>
              <tbody>
                {filtered.map((book) => (
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
        </div>
      )
    }

    if (activePage === 'account') {
      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">Change Password</div></div>
          <form className="admin-form" onSubmit={handleChangePassword}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%' }}>
              <div className="frow">
                <div className="fgroup"><label>Current password</label><input type="password" value={passwordForm.old_password} onChange={(event) => { setPasswordForm({ ...passwordForm, old_password: event.target.value }); setPasswordError(''); }} placeholder="Current password" /></div>
                <div className="fgroup"><label>New password</label><input type="password" value={passwordForm.new_password} onChange={(event) => { setPasswordForm({ ...passwordForm, new_password: event.target.value }); setPasswordError(''); }} placeholder="New password" /></div>
              </div>
              <button className="btn btn-blue" type="submit" style={{ alignSelf: 'flex-start' }}>Save password</button>
              {passwordError && <div className="password-error">{passwordError}</div>}
            </div>
          </form>
        </div>
      )
    }

    return null
  }

  return (
    <div className="librarian-dashboard-app">
      <div className="sidebar">
        <div className="logo">
          <div className="logo-icon">📚</div>
          <div className="logo-title">LIBRASYS</div>
          <div className="logo-sub">Librarian</div>
        </div>
        <nav className="nav">
          {navigationSections.map((section) => (
            <div key={section.section}>
              <div className="nav-section">{section.section}</div>
              {section.items.map((item) => (
                <div key={item.id} className={`nav-item ${activePage === item.id ? 'active' : ''}`} onClick={() => setActivePage(item.id)}>
                  <span className="nav-icon">{item.icon}</span>
                  <span>{item.title}</span>
                  {item.badge && <span className="nav-badge">{item.badge}</span>}
                </div>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="avatar">LI</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '12px', color: 'var(--text)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>Librarian</div>
              <div style={{ fontSize: '10px', color: 'var(--muted)' }}>librarian@librasys.edu</div>
            </div>
            <span style={{ cursor: 'pointer', fontSize: '14px', color: 'var(--red)' }} title="Logout" onClick={() => setShowLogoutConfirm(true)}>⏻</span>
          </div>
        </div>
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
          <div className="search-wrap">
            <input className="search-input" value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder="Search..." />
          </div>
          <div style={{ position: 'relative' }}>
            <span style={{ fontSize: '18px', cursor: 'pointer', position: 'relative' }} onClick={() => setShowNotifications(!showNotifications)}>
              🔔
              {notifications.length > 0 && <span className="notif-badge">{notifications.length}</span>}
            </span>
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
          <div className="avatar">LI</div>
        </div>
        <div className="content">
          {renderPage()}
        </div>
      </div>
      {showPasswordModal && (
        <div className="modal-overlay" onClick={() => setShowPasswordModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">Success</div>
            </div>
            <div className="modal-body">
              <div className="modal-message">Password changed successfully!</div>
            </div>
            <div className="modal-footer">
              <button className="btn-close" onClick={() => setShowPasswordModal(false)}>OK</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
