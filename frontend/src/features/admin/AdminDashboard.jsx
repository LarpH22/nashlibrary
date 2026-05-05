import { useEffect, useMemo, useState } from 'react'
import { BookOpen, LogOut, Bell, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import {
  fetchCategories,
  createCategory,
  deleteCategory,
  fetchAuthors,
  createAuthor,
  deleteAuthor,
  fetchBooks,
  createBook,
  borrowBook,
  returnBook,
  fetchStudent,
  fetchStudents,
  updateStudent,
  resetStudentPassword,
  fetchLoans,
  fetchAdminFines,
  updateFineStatus,
  changePassword,
  fetchRegistrationRequests,
  fetchRegistrationDocument,
  approveRegistration,
  rejectRegistration
} from './adminService.js'
import { clearStoredAuth } from '../../shared/authStorage.js'
import './AdminDashboard.css'

const navSections = [
  {
    section: 'MAIN',
    items: [
      { id: 'overview', icon: '📊', title: 'Overview' },
      { id: 'registrations', icon: '📝', title: 'Registration Requests' },
      { id: 'books', icon: '📖', title: 'Books' },
      { id: 'loans', icon: '🔄', title: 'Issue / Return', badge: '3' },
      { id: 'students', icon: '👥', title: 'Students' }
    ]
  },
  {
    section: 'LIBRARY',
    items: [
      { id: 'categories', icon: '🗂', title: 'Categories' },
      { id: 'authors', icon: '✍️', title: 'Authors' }
    ]
  },
  {
    section: 'ACCOUNT',
    items: [
      { id: 'account', icon: '🔑', title: 'Change Password' }
    ]
  }
]

navSections[0].items.splice(4, 0, { id: 'fines', icon: '$', title: 'Fines' })

const pageTitles = {
  overview: 'Overview',
  registrations: 'Registration Requests',
  books: 'Books',
  loans: 'Issue / Return',
  fines: 'Fines Management',
  students: 'Students',
  categories: 'Categories',
  authors: 'Authors',
  account: 'Change Password'
}

const bookInventoryPageSize = 10
const emptyStudentForm = {
  student_id: '',
  full_name: '',
  email: '',
  student_number: '',
  department: '',
  year_level: '',
  status: 'active',
  email_verified: false,
  registration_document: '',
  document_url: '',
  document_exists: false
}

export function AdminDashboard() {
  const navigate = useNavigate()
  const [activePage, setActivePage] = useState('overview')
  const [categories, setCategories] = useState([])
  const [authors, setAuthors] = useState([])
  const [books, setBooks] = useState([])
  const [loans, setLoans] = useState([])
  const [students, setStudents] = useState([])
  const [fines, setFines] = useState([])
  const [fineSummary, setFineSummary] = useState({ total_count: 0, unpaid_count: 0, paid_count: 0, total_unpaid: 0, total_paid: 0 })
  const [fineStatusMessage, setFineStatusMessage] = useState('')
  const [updatingFineId, setUpdatingFineId] = useState(null)
  const [studentId, setStudentId] = useState('')
  const [student, setStudent] = useState(null)
  const [editingStudent, setEditingStudent] = useState(null)
  const [studentForm, setStudentForm] = useState(emptyStudentForm)
  const [studentFormError, setStudentFormError] = useState('')
  const [studentPasswordForm, setStudentPasswordForm] = useState({ student_id: '', new_password: '' })
  const [studentPasswordMessage, setStudentPasswordMessage] = useState('')
  const [, setMessage] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [showPasswordSuccessModal, setShowPasswordSuccessModal] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [categoryName, setCategoryName] = useState('')
  const [authorName, setAuthorName] = useState('')
  const [bookForm, setBookForm] = useState({ title: '', author: '', isbn: '', available_copies: '1', total_copies: '1' })
  const [borrowForm, setBorrowForm] = useState({ book_id: '', user_id: '' })
  const [returnLoanId, setReturnLoanId] = useState('')
  const [passwordForm, setPasswordForm] = useState({ old_password: '', new_password: '' })
  const [registrationRequests, setRegistrationRequests] = useState([])
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)
  const [bookInventoryPage, setBookInventoryPage] = useState(1)
  const [notifications, setNotifications] = useState([])
  const [showNotifications, setShowNotifications] = useState(false)
  const adminEmail = localStorage.getItem('user_email') || 'admin@librasys.edu'

  useEffect(() => {
    loadCategories()
    loadAuthors()
    loadBooks()
    loadLoans()
    loadStudents()
    loadFines()
    loadRegistrationRequests()
  }, [])

  const handleLogout = () => {
    clearStoredAuth()
    navigate('/login', { replace: true })
  }

  const handlePasswordSuccessConfirm = () => {
    setShowPasswordSuccessModal(false)
    clearStoredAuth()
    navigate('/login', { replace: true })
  }

  const removeNotification = (id) => {
    setNotifications((prev) => prev.filter((notif) => notif.id !== id))
  }

  const stats = useMemo(
    () => [
      { label: 'Categories', value: categories.length, type: 'gold' },
      { label: 'Authors', value: authors.length, type: 'blue' },
      { label: 'Books', value: books.length, type: 'green' },
      { label: 'Loans', value: loans.length, type: 'purple' },
      { label: 'Students', value: students.length, type: 'blue' },
      { label: 'Unpaid Fines', value: `$${Number(fineSummary.total_unpaid || 0).toFixed(2)}`, type: 'red' }
    ],
    [categories, authors, books, loans, students, fineSummary.total_unpaid]
  )

  const normalizedSearchQuery = searchQuery.trim().toLowerCase()
  const matchesSearch = (...values) => {
    if (!normalizedSearchQuery) {
      return true
    }
    return values.some((value) => String(value || '').toLowerCase().includes(normalizedSearchQuery))
  }

  const filteredRegistrationRequests = registrationRequests.filter((request) =>
    matchesSearch(request.full_name, request.email, request.student_number, request.department, request.year_level)
  )
  const filteredCategories = categories.filter((category) => matchesSearch(category.name))
  const filteredAuthors = authors.filter((author) => matchesSearch(author.name))
  const filteredBooks = books.filter((book) => matchesSearch(book.title, book.author, book.isbn))
  const filteredLoans = loans.filter((loan) => matchesSearch(loan.loan_id, loan.book_title, loan.student_name, loan.status))
  const filteredStudents = students.filter((studentRow) =>
    matchesSearch(studentRow.full_name, studentRow.email, studentRow.student_number, studentRow.status, studentRow.department)
  )
  const filteredFines = fines.filter((fine) =>
    matchesSearch(fine.fine_id, fine.loan_id, fine.student_name, fine.student_number, fine.book_title, fine.status)
  )

  const bookInventoryPageNumbers = (totalPages, currentPage) => {
    const start = Math.max(1, currentPage - 2)
    const end = Math.min(totalPages, start + 4)
    const adjustedStart = Math.max(1, end - 4)

    return Array.from({ length: end - adjustedStart + 1 }, (_, index) => adjustedStart + index)
  }

  async function loadCategories() {
    try {
      setCategories(await fetchCategories())
    } catch {
      setMessage('Unable to load categories.')
    }
  }

  async function loadAuthors() {
    try {
      setAuthors(await fetchAuthors())
    } catch {
      setMessage('Unable to load authors.')
    }
  }

  async function loadBooks() {
    try {
      setBooks(await fetchBooks())
    } catch {
      setMessage('Unable to load books.')
    }
  }

  async function loadLoans() {
    try {
      setLoans(await fetchLoans())
    } catch {
      setMessage('Unable to load loans.')
    }
  }

  async function loadStudents() {
    try {
      setStudents(await fetchStudents())
    } catch {
      setMessage('Unable to load students.')
    }
  }

  async function loadFines() {
    try {
      const data = await fetchAdminFines()
      setFines(Array.isArray(data?.fines) ? data.fines : [])
      setFineSummary(data?.summary || { total_count: 0, unpaid_count: 0, paid_count: 0, total_unpaid: 0, total_paid: 0 })
    } catch {
      setMessage('Unable to load fines.')
    }
  }

  async function handleFineStatusChange(fineId, status) {
    setUpdatingFineId(fineId)
    setFineStatusMessage('')
    try {
      await updateFineStatus(fineId, status)
      await loadFines()
      setFineStatusMessage(`Fine marked as ${status}.`)
    } catch (error) {
      setFineStatusMessage(error?.response?.data?.message || 'Unable to update fine status.')
    } finally {
      setUpdatingFineId(null)
    }
  }

  async function loadRegistrationRequests() {
    try {
      setRegistrationRequests(await fetchRegistrationRequests())
    } catch {
      setMessage('Unable to load registration requests.')
    }
  }

  async function handleAddCategory(event) {
    event.preventDefault()
    if (!categoryName.trim()) return
    try {
      await createCategory(categoryName)
      setCategoryName('')
      await loadCategories()
      setMessage('Category saved successfully.')
    } catch {
      setMessage('Failed to save category.')
    }
  }

  async function handleAddAuthor(event) {
    event.preventDefault()
    if (!authorName.trim()) return
    try {
      await createAuthor(authorName)
      setAuthorName('')
      await loadAuthors()
      setMessage('Author saved successfully.')
    } catch {
      setMessage('Failed to save author.')
    }
  }

  async function handleAddBook(event) {
    event.preventDefault()
    try {
      await createBook({
        ...bookForm,
        available_copies: Number(bookForm.available_copies || 1),
        total_copies: Number(bookForm.total_copies || 1)
      })
      setBookForm({ title: '', author: '', isbn: '', available_copies: '1', total_copies: '1' })
      await loadBooks()
      setMessage('Book created successfully.')
    } catch {
      setMessage('Failed to create book.')
    }
  }

  async function handleBorrowBook(event) {
    event.preventDefault()
    try {
      await borrowBook(Number(borrowForm.book_id), Number(borrowForm.user_id))
      setBorrowForm({ book_id: '', user_id: '' })
      await Promise.all([loadBooks(), loadLoans()])
      setMessage('Book issued successfully.')
    } catch (err) {
      await Promise.allSettled([loadBooks(), loadLoans()])
      setMessage(err?.response?.data?.message || 'Failed to issue book.')
    }
  }

  async function handleReturnBook(event) {
    event.preventDefault()
    try {
      await returnBook(Number(returnLoanId))
      setReturnLoanId('')
      await Promise.all([loadBooks(), loadLoans()])
      setMessage('Book return recorded.')
    } catch (err) {
      await Promise.allSettled([loadBooks(), loadLoans()])
      setMessage(err?.response?.data?.message || 'Failed to return book.')
    }
  }

  async function handleSearchStudent(event) {
    event.preventDefault()
    const trimmedId = studentId.trim()
    if (!trimmedId) return
    try {
      const found = await fetchStudent(trimmedId)
      setStudent(found)
      setMessage('Student record loaded.')
    } catch {
      setStudent(null)
      setMessage('Student not found.')
    }
  }

  function openEditStudent(studentRow) {
    setEditingStudent(studentRow)
    setStudentForm({
      student_id: studentRow.student_id || studentRow.user_id || '',
      full_name: studentRow.full_name || '',
      email: studentRow.email || '',
      student_number: studentRow.student_number || '',
      department: studentRow.department || '',
      year_level: studentRow.year_level || '',
      status: studentRow.status || 'active',
      email_verified: Boolean(studentRow.email_verified),
      registration_document: studentRow.registration_document || '',
      document_url: studentRow.document_url || '',
      document_exists: Boolean(studentRow.document_exists)
    })
    setStudentFormError('')
    setStudentPasswordForm({ student_id: '', new_password: '' })
    setStudentPasswordMessage('')
  }

  function validateStudentForm() {
    if (!studentForm.full_name.trim()) {
      return 'Full name is required.'
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(studentForm.email.trim())) {
      return 'Enter a valid email address.'
    }
    if (!/^\d{3}-\d{4}$/.test(studentForm.student_number.trim())) {
      return 'Student ID must use format 241-0449.'
    }
    if (!['active', 'inactive', 'suspended', 'pending'].includes(studentForm.status)) {
      return 'Choose a valid account status.'
    }
    if (studentForm.year_level) {
      const yearLevel = Number(studentForm.year_level)
      if (!Number.isInteger(yearLevel) || yearLevel < 1 || yearLevel > 6) {
        return 'Year level must be a whole number from 1 to 6.'
      }
    }
    return ''
  }

  async function handleSaveStudent(event) {
    event.preventDefault()
    const validationError = validateStudentForm()
    if (validationError) {
      setStudentFormError(validationError)
      return
    }
    if (!window.confirm('Save changes to this student account?')) {
      return
    }
    try {
      const updated = await updateStudent(studentForm.student_id, {
        full_name: studentForm.full_name.trim(),
        email: studentForm.email.trim(),
        student_number: studentForm.student_number.trim(),
        department: studentForm.department.trim(),
        year_level: studentForm.year_level ? Number(studentForm.year_level) : '',
        status: studentForm.status,
        email_verified: studentForm.email_verified
      })
      await loadStudents()
      setStudent(updated)
      setEditingStudent(null)
      setStudentForm(emptyStudentForm)
      setStudentFormError('')
      setMessage('Student account updated.')
    } catch (error) {
      setStudentFormError(error?.response?.data?.message || 'Unable to update student.')
    }
  }

  async function handleResetStudentPassword(event) {
    event.preventDefault()
    setStudentPasswordMessage('')
    if (studentPasswordForm.new_password.length < 8) {
      setStudentPasswordMessage('Password must be at least 8 characters.')
      return
    }
    if (!window.confirm('Reset this student password now?')) {
      return
    }
    try {
      await resetStudentPassword(studentPasswordForm.student_id, studentPasswordForm.new_password)
      setStudentPasswordForm({ student_id: '', new_password: '' })
      setStudentPasswordMessage('Password reset successfully.')
    } catch (error) {
      setStudentPasswordMessage(error?.response?.data?.message || 'Unable to reset password.')
    }
  }

  async function handleChangePassword(event) {
    event.preventDefault()
    setPasswordError('')

    if (!passwordForm.old_password || !passwordForm.new_password) {
      setPasswordError('Both password fields are required.')
      return
    }

    if (passwordForm.new_password.length < 6) {
      setPasswordError('New password must be at least 6 characters long.')
      return
    }

    try {
      await changePassword(passwordForm.old_password, passwordForm.new_password)
      setPasswordForm({ old_password: '', new_password: '' })
      setPasswordError('')
      setShowPasswordSuccessModal(true)
    } catch (error) {
      console.error('Password change error:', error)
      const responseData = error.response?.data
      const errorMsg = typeof responseData === 'string'
        ? responseData
        : responseData?.message || responseData?.error || error.message || 'Password change failed.'
      setPasswordError(errorMsg)
    }
  }

  async function handleViewDocument(documentUrl) {
    if (!documentUrl) {
      window.alert('No document is available for this student.')
      return
    }

    const previewWindow = window.open('', '_blank')
    if (previewWindow) {
      previewWindow.document.write('<!doctype html><title>Loading document...</title><body style="font-family:sans-serif;padding:24px">Loading document...</body>')
      previewWindow.document.close()
    }
    try {
      const blob = await fetchRegistrationDocument(documentUrl)
      const objectUrl = URL.createObjectURL(blob)
      if (previewWindow) {
        previewWindow.opener = null
        previewWindow.location.replace(objectUrl)
      } else {
        const link = document.createElement('a')
        link.href = objectUrl
        link.target = '_blank'
        link.rel = 'noopener noreferrer'
        document.body.appendChild(link)
        link.click()
        link.remove()
      }
      setTimeout(() => URL.revokeObjectURL(objectUrl), 10000)
    } catch (error) {
      if (previewWindow) {
        previewWindow.document.body.innerHTML = '<div style="font-family:sans-serif;padding:24px">Unable to load registration document.</div>'
      }
      const message = error?.response?.data?.message || 'Unable to load registration document.'
      window.alert(message)
    }
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
                <div className="stat-sub">Current total</div>
                <div className="stat-icon">{stat.label === 'Books' ? '📚' : stat.label === 'Loans' ? '🔄' : stat.label === 'Authors' ? '✍️' : '🗂'}</div>
              </div>
            ))}
          </div>
          <div className="grid2">
            <div className="card">
              <div className="card-hdr">
                <div className="card-title">Overview</div>
              </div>
              <p>Welcome to the admin dashboard. Use the sidebar to manage books, loans, students, categories, and authors.</p>
            </div>
            <div className="card">
              <div className="card-hdr">
                <div className="card-title">Quick Actions</div>
              </div>
              <div style={{ display: 'grid', gap: '10px' }}>
                <button className="btn btn-gold" type="button" onClick={() => setActivePage('categories')}>Add Category</button>
                <button className="btn btn-outline" type="button" onClick={() => setActivePage('authors')}>Add Author</button>
                <button className="btn btn-outline" type="button" onClick={() => setActivePage('books')}>Add Book</button>
              </div>
            </div>
          </div>
        </>
      )
    }

    if (activePage === 'registrations') {
      return (
        <div className="card">
          <div className="card-hdr">
            <div className="card-title">Registration Requests ({filteredRegistrationRequests.length})</div>
          </div>
          <p className="subtext">Review submitted student registration requests and verify the uploaded student documentation before approving access.</p>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Student ID</th>
                  <th>Department / Program</th>
                  <th>Year Level</th>
                  <th>Verified</th>
                  <th>Document</th>
                  <th>Submitted</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredRegistrationRequests.map((request) => (
                  <tr key={request.request_id}>
                    <td>{request.full_name}</td>
                    <td>{request.email}</td>
                    <td>{request.student_number}</td>
                    <td>{request.department || ''}</td>
                    <td>{request.year_level || ''}</td>
                    <td>{request.email_verified ? '✅' : '❌'}</td>
                    <td>
                      {request.document_url ? (
                        <button
                          className="btn btn-outline btn-sm"
                          type="button"
                          onClick={() => handleViewDocument(request.document_url)}
                        >
                          View Document
                        </button>
                      ) : (
                        'No document'
                      )}
                    </td>
                    <td>{new Date(request.created_at).toLocaleDateString()}</td>
                    <td>
                      <button
                        className="btn btn-gold btn-sm"
                        type="button"
                        onClick={async () => {
                          try {
                            await approveRegistration(request.request_id)
                            await loadRegistrationRequests()
                            setMessage('Registration approved successfully.')
                          } catch {
                            setMessage('Failed to approve registration.')
                          }
                        }}
                      >
                        Approve
                      </button>
                      <button
                        className="btn btn-outline btn-sm"
                        type="button"
                        onClick={async () => {
                          try {
                            await rejectRegistration(request.request_id)
                            await loadRegistrationRequests()
                            setMessage('Registration rejected.')
                          } catch {
                            setMessage('Failed to reject registration.')
                          }
                        }}
                      >
                        Reject
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )
    }

    if (activePage === 'categories') {
      return (
        <div className="card">
          <div className="card-hdr">
            <div className="card-title">Category Management ({filteredCategories.length})</div>
          </div>
          <form className="admin-form" onSubmit={handleAddCategory}>
            <div className="fgroup" style={{ flex: 1 }}>
              <label>New category</label>
              <input value={categoryName} onChange={(event) => setCategoryName(event.target.value)} placeholder="Category name" />
            </div>
            <button className="btn btn-gold" type="submit">Add Category</button>
          </form>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr><th>Name</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {filteredCategories.map((category) => (
                  <tr key={category.category_id}>
                    <td>{category.name}</td>
                    <td>
                      <button className="btn btn-outline btn-sm" type="button" onClick={async () => { await deleteCategory(category.category_id); await loadCategories() }}>Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )
    }

    if (activePage === 'authors') {
      return (
        <div className="card">
          <div className="card-hdr">
            <div className="card-title">Author Management ({filteredAuthors.length})</div>
          </div>
          <form className="admin-form" onSubmit={handleAddAuthor}>
            <div className="fgroup" style={{ flex: 1 }}>
              <label>New author</label>
              <input value={authorName} onChange={(event) => setAuthorName(event.target.value)} placeholder="Author name" />
            </div>
            <button className="btn btn-gold" type="submit">Add Author</button>
          </form>
          <div className="admin-table-container">
            <table>
              <thead>
                <tr><th>Name</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {filteredAuthors.map((author) => (
                  <tr key={author.author_id}>
                    <td>{author.name}</td>
                    <td>
                      <button className="btn btn-outline btn-sm" type="button" onClick={async () => { await deleteAuthor(author.author_id); await loadAuthors() }}>Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )
    }

    if (activePage === 'books') {
      const totalPages = Math.max(1, Math.ceil(filteredBooks.length / bookInventoryPageSize))
      const currentPage = Math.min(Math.max(1, bookInventoryPage || 1), totalPages)
      const firstResult = filteredBooks.length === 0 ? 0 : ((currentPage - 1) * bookInventoryPageSize) + 1
      const lastResult = Math.min(currentPage * bookInventoryPageSize, filteredBooks.length)
      const visibleBooks = filteredBooks.slice((currentPage - 1) * bookInventoryPageSize, currentPage * bookInventoryPageSize)

      return (
        <>
          <div className="card">
            <div className="card-hdr">
              <div className="card-title">Add New Book</div>
            </div>
            <form className="admin-form" onSubmit={handleAddBook}>
              <div className="frow">
                <div className="fgroup">
                  <label>Title</label>
                  <input value={bookForm.title} onChange={(event) => setBookForm((current) => ({ ...current, title: event.target.value }))} placeholder="Title" />
                </div>
                <div className="fgroup">
                  <label>Author</label>
                  <input value={bookForm.author} onChange={(event) => setBookForm((current) => ({ ...current, author: event.target.value }))} placeholder="Author" />
                </div>
              </div>
              <div className="frow">
                <div className="fgroup">
                  <label>ISBN</label>
                  <input value={bookForm.isbn} onChange={(event) => setBookForm((current) => ({ ...current, isbn: event.target.value }))} placeholder="ISBN" />
                </div>
                <div className="fgroup">
                  <label>Available copies</label>
                  <input type="number" min="1" value={bookForm.available_copies} onChange={(event) => setBookForm((current) => ({ ...current, available_copies: event.target.value }))} />
                </div>
              </div>
              <div className="frow">
                <div className="fgroup">
                  <label>Total copies</label>
                  <input type="number" min="1" value={bookForm.total_copies} onChange={(event) => setBookForm((current) => ({ ...current, total_copies: event.target.value }))} />
                </div>
                <div className="fgroup" style={{ alignSelf: 'end' }}>
                  <button className="btn btn-gold" type="submit">Save Book</button>
                </div>
              </div>
            </form>
          </div>
          <div className="card">
            <div className="card-hdr">
              <div className="card-title">Book Inventory</div>
              <div className="inventory-count">
                {filteredBooks.length > 0 ? `${firstResult}-${lastResult} of ${filteredBooks.length} records` : '0 records'}
              </div>
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
                      <td>{book.author}</td>
                      <td>{book.isbn}</td>
                      <td>{book.available_copies}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {books.length > bookInventoryPageSize && (
              <div className="pagination-bar">
                <button className="btn btn-outline btn-sm" type="button" disabled={currentPage <= 1} onClick={() => setBookInventoryPage(currentPage - 1)}>Previous</button>
                <div className="page-buttons">
                  {bookInventoryPageNumbers(totalPages, currentPage).map((page) => (
                    <button
                      key={page}
                      className={`page-button ${page === currentPage ? 'active' : ''}`}
                      type="button"
                      onClick={() => setBookInventoryPage(page)}
                    >
                      {page}
                    </button>
                  ))}
                </div>
                <button className="btn btn-outline btn-sm" type="button" disabled={currentPage >= totalPages} onClick={() => setBookInventoryPage(currentPage + 1)}>Next</button>
                <span className="pagination-summary">Page {currentPage} of {totalPages}</span>
              </div>
            )}
          </div>
        </>
      )
    }

    if (activePage === 'loans') {
      return (
        <>
          <div className="grid2">
            <div className="card">
              <div className="card-hdr">
                <div className="card-title">Issue Book</div>
              </div>
              <form className="admin-form" onSubmit={handleBorrowBook}>
                <div className="fgroup"><label>Book ID</label><input value={borrowForm.book_id} onChange={(event) => setBorrowForm((current) => ({ ...current, book_id: event.target.value }))} placeholder="Book ID" /></div>
                <div className="fgroup"><label>Student ID</label><input value={borrowForm.user_id} onChange={(event) => setBorrowForm((current) => ({ ...current, user_id: event.target.value }))} placeholder="Student ID" /></div>
                <button className="btn btn-gold" type="submit">Issue</button>
              </form>
            </div>
            <div className="card">
              <div className="card-hdr">
                <div className="card-title">Return Book</div>
              </div>
              <form className="admin-form" onSubmit={handleReturnBook}>
                <div className="fgroup"><label>Loan ID</label><input value={returnLoanId} onChange={(event) => setReturnLoanId(event.target.value)} placeholder="Loan ID" /></div>
                <button className="btn btn-gold" type="submit">Return</button>
              </form>
            </div>
          </div>
          <div className="card">
            <div className="card-hdr"><div className="card-title">Current Loans ({filteredLoans.length})</div></div>
            <div className="admin-table-container">
              <table>
                <thead>
                  <tr><th>Loan ID</th><th>Book</th><th>Student</th><th>Status</th></tr>
                </thead>
                <tbody>
                  {filteredLoans.map((loan) => (
                    <tr key={loan.loan_id}>
                      <td>{loan.loan_id}</td>
                      <td>{loan.book_title || loan.book_id}</td>
                      <td>{loan.student_name || loan.user_id || loan.student_id}</td>
                      <td>{loan.status || (loan.returned ? 'Returned' : 'Active')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )
    }

    if (activePage === 'fines') {
      const unpaidFines = filteredFines.filter((fine) => fine.status === 'unpaid')
      const paidFines = filteredFines.filter((fine) => fine.status === 'paid')

      return (
        <>
          <div className="grid4">
            <div className="stat red">
              <div className="stat-label">Unpaid</div>
              <div className="stat-num">{fineSummary.unpaid_count || 0}</div>
              <div className="stat-sub">${Number(fineSummary.total_unpaid || 0).toFixed(2)}</div>
            </div>
            <div className="stat green">
              <div className="stat-label">Paid</div>
              <div className="stat-num">{fineSummary.paid_count || 0}</div>
              <div className="stat-sub">${Number(fineSummary.total_paid || 0).toFixed(2)}</div>
            </div>
            <div className="stat blue">
              <div className="stat-label">Total Fines</div>
              <div className="stat-num">{fineSummary.total_count || fines.length}</div>
              <div className="stat-sub">Recorded payments</div>
            </div>
            <div className="stat gold">
              <div className="stat-label">Visible</div>
              <div className="stat-num">{filteredFines.length}</div>
              <div className="stat-sub">Search results</div>
            </div>
          </div>

          <div className="card">
            <div className="card-hdr">
              <div>
                <div className="card-title">Walk-in Fine Payments ({filteredFines.length})</div>
                <div className="subtext">Mark payments after receiving cash or in-person payment from a student.</div>
              </div>
              <button className="btn btn-outline btn-sm" type="button" onClick={loadFines}>Refresh</button>
            </div>
            {fineStatusMessage && <div className="status-message">{fineStatusMessage}</div>}
            <div className="admin-table-container">
              <table>
                <thead>
                  <tr>
                    <th>Fine ID</th>
                    <th>Student</th>
                    <th>Book</th>
                    <th>Loan</th>
                    <th>Overdue</th>
                    <th>Amount</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredFines.length === 0 ? (
                    <tr><td colSpan="8" className="empty-cell">No fines found.</td></tr>
                  ) : filteredFines.map((fine) => {
                    const isPaid = fine.status === 'paid'
                    const isUpdating = updatingFineId === fine.fine_id
                    return (
                      <tr key={fine.fine_id}>
                        <td>{fine.fine_id}</td>
                        <td>
                          <strong>{fine.student_name || 'Unknown student'}</strong>
                          <div className="muted-line">{fine.student_number || fine.student_email || `Student ${fine.student_id}`}</div>
                        </td>
                        <td>
                          {fine.book_title || fine.book_id || 'Unknown book'}
                          <div className="muted-line">{fine.copy_code || ''}</div>
                        </td>
                        <td>{fine.loan_id}</td>
                        <td>{Number(fine.days_overdue || 0)} day{Number(fine.days_overdue || 0) === 1 ? '' : 's'}</td>
                        <td>${Number(fine.amount || 0).toFixed(2)}</td>
                        <td><span className={`fine-pill ${isPaid ? 'paid' : 'unpaid'}`}>{isPaid ? 'Paid' : 'Unpaid'}</span></td>
                        <td>
                          <button
                            className="btn btn-gold btn-sm"
                            type="button"
                            disabled={isUpdating || isPaid}
                            onClick={() => handleFineStatusChange(fine.fine_id, 'paid')}
                          >
                            Paid
                          </button>
                          <button
                            className="btn btn-outline btn-sm"
                            type="button"
                            disabled={isUpdating || !isPaid}
                            onClick={() => handleFineStatusChange(fine.fine_id, 'unpaid')}
                          >
                            Unpaid
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            <div className="fine-summary-line">
              Showing {unpaidFines.length} unpaid and {paidFines.length} paid fine{filteredFines.length === 1 ? '' : 's'}.
            </div>
          </div>
        </>
      )
    }

    if (activePage === 'students') {
      return (
        <>
          <div className="card">
            <div className="card-hdr">
              <div>
                <div className="card-title">Student Management</div>
                <div className="subtext">View registered students, edit account details, open submitted documents, and reset passwords when needed.</div>
              </div>
              <button className="btn btn-outline btn-sm" type="button" onClick={loadStudents}>Refresh</button>
            </div>
            {studentFormError && <div className="status-message error-message">{studentFormError}</div>}
            {studentPasswordMessage && <div className="status-message">{studentPasswordMessage}</div>}
            <div className="admin-table-container">
              <table>
                <thead>
                  <tr>
                    <th>Student</th>
                    <th>Email</th>
                    <th>Department / Year</th>
                    <th>Account</th>
                    <th>Verified</th>
                    <th>Document</th>
                    <th>Last Login</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredStudents.length === 0 ? (
                    <tr><td colSpan="8" className="empty-cell">No registered students found.</td></tr>
                  ) : filteredStudents.map((studentRow) => (
                    <tr key={studentRow.student_id || studentRow.user_id || studentRow.student_number}>
                      <td>
                        <strong>{studentRow.full_name || 'Unnamed student'}</strong>
                        <div className="muted-line">{studentRow.student_number || `Student ${studentRow.student_id || studentRow.user_id}`}</div>
                      </td>
                      <td>{studentRow.email || '-'}</td>
                      <td>
                        {studentRow.department || '-'}
                        <div className="muted-line">{studentRow.year_level ? `Year ${studentRow.year_level}` : 'Year not set'}</div>
                      </td>
                      <td><span className={`student-pill ${studentRow.status || 'active'}`}>{studentRow.status || 'active'}</span></td>
                      <td>{studentRow.email_verified ? 'Verified' : 'Not verified'}</td>
                      <td>
                        {studentRow.document_url && studentRow.document_exists ? (
                          <button className="btn btn-outline btn-sm" type="button" onClick={() => handleViewDocument(studentRow.document_url)}>View</button>
                        ) : studentRow.registration_document ? (
                          <span className="missing-document">Missing</span>
                        ) : '-'}
                      </td>
                      <td>{studentRow.last_login || '-'}</td>
                      <td>
                        <div className="row-actions">
                          <button className="btn btn-gold btn-sm" type="button" onClick={() => openEditStudent(studentRow)}>Edit</button>
                          <button className="btn btn-outline btn-sm" type="button" onClick={() => {
                            setStudentPasswordForm({ student_id: studentRow.student_id || studentRow.user_id || '', new_password: '' })
                            setStudentPasswordMessage('')
                          }}>Reset Password</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="fine-summary-line">
              Showing {filteredStudents.length} of {students.length} registered student{students.length === 1 ? '' : 's'}.
            </div>
          </div>

          <div className="card">
            <div className="card-hdr"><div className="card-title">Student Lookup</div></div>
            <form className="admin-form" onSubmit={handleSearchStudent}>
              <div className="frow lookup-row">
                <div className="fgroup">
                  <label>Student ID</label>
                  <input value={studentId} onChange={(event) => setStudentId(event.target.value)} placeholder="241-0449" />
                </div>
                <div className="lookup-button-cell">
                  <button className="btn btn-gold" type="submit">Search</button>
                </div>
              </div>
            </form>
            {student && (
              <div className="student-detail-strip">
                <div>
                  <strong>{student.full_name || student.name || 'Unnamed student'}</strong>
                  <div className="muted-line">{student.student_number || student.user_id || student.student_id || '-'}</div>
                </div>
                <div>{student.email || '-'}</div>
                <div><span className={`student-pill ${student.status || 'active'}`}>{student.status || 'active'}</span></div>
                <button className="btn btn-outline btn-sm" type="button" onClick={() => openEditStudent(student)}>Edit</button>
              </div>
            )}
          </div>

          {editingStudent && (
            <div className="modal-overlay">
              <div className="admin-modal">
                <div className="modal-header">
                  <div>
                    <div className="modal-title">Edit Student</div>
                    <div className="subtext">{editingStudent.student_number || editingStudent.email}</div>
                  </div>
                  <button className="icon-button" type="button" onClick={() => setEditingStudent(null)} aria-label="Close edit student">
                    <X size={18} aria-hidden="true" />
                  </button>
                </div>
                <form onSubmit={handleSaveStudent}>
                  <div className="frow">
                    <div className="fgroup">
                      <label>Full name</label>
                      <input value={studentForm.full_name} onChange={(event) => setStudentForm({ ...studentForm, full_name: event.target.value })} />
                    </div>
                    <div className="fgroup">
                      <label>Email</label>
                      <input value={studentForm.email} onChange={(event) => setStudentForm({ ...studentForm, email: event.target.value })} />
                    </div>
                  </div>
                  <div className="frow">
                    <div className="fgroup">
                      <label>Student ID</label>
                      <input value={studentForm.student_number} onChange={(event) => setStudentForm({ ...studentForm, student_number: event.target.value })} placeholder="241-0449" />
                    </div>
                    <div className="fgroup">
                      <label>Department</label>
                      <input value={studentForm.department} onChange={(event) => setStudentForm({ ...studentForm, department: event.target.value })} />
                    </div>
                  </div>
                  <div className="frow">
                    <div className="fgroup">
                      <label>Year level</label>
                      <input type="number" min="1" max="6" value={studentForm.year_level} onChange={(event) => setStudentForm({ ...studentForm, year_level: event.target.value })} />
                    </div>
                    <div className="fgroup">
                      <label>Account status</label>
                      <select value={studentForm.status} onChange={(event) => setStudentForm({ ...studentForm, status: event.target.value })}>
                        <option value="active">Active</option>
                        <option value="pending">Pending</option>
                        <option value="inactive">Inactive</option>
                        <option value="suspended">Suspended</option>
                      </select>
                    </div>
                  </div>
                  <label className="check-row">
                    <input type="checkbox" checked={studentForm.email_verified} onChange={(event) => setStudentForm({ ...studentForm, email_verified: event.target.checked })} />
                    Email verified
                  </label>
                  <div className="document-row">
                    <span>{studentForm.registration_document || 'No registration document uploaded.'}</span>
                    {studentForm.document_url && studentForm.document_exists && <button className="btn btn-outline btn-sm" type="button" onClick={() => handleViewDocument(studentForm.document_url)}>View Document</button>}
                    {studentForm.registration_document && !studentForm.document_exists && <span className="missing-document">File missing</span>}
                  </div>
                  {studentFormError && <div className="form-error">{studentFormError}</div>}
                  <div className="modal-actions">
                    <button className="btn btn-outline" type="button" onClick={() => setEditingStudent(null)}>Cancel</button>
                    <button className="btn btn-gold" type="submit">Save Changes</button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {studentPasswordForm.student_id && !editingStudent && (
            <div className="modal-overlay">
              <div className="admin-modal small-modal">
                <div className="modal-header">
                  <div>
                    <div className="modal-title">Reset Student Password</div>
                    <div className="subtext">This immediately updates the student login password.</div>
                  </div>
                  <button className="icon-button" type="button" onClick={() => setStudentPasswordForm({ student_id: '', new_password: '' })} aria-label="Close reset password">
                    <X size={18} aria-hidden="true" />
                  </button>
                </div>
                <form onSubmit={handleResetStudentPassword}>
                  <div className="fgroup">
                    <label>New password</label>
                    <input type="password" value={studentPasswordForm.new_password} onChange={(event) => setStudentPasswordForm({ ...studentPasswordForm, new_password: event.target.value })} placeholder="At least 8 characters" />
                  </div>
                  {studentPasswordMessage && <div className="form-error">{studentPasswordMessage}</div>}
                  <div className="modal-actions">
                    <button className="btn btn-outline" type="button" onClick={() => setStudentPasswordForm({ student_id: '', new_password: '' })}>Cancel</button>
                    <button className="btn btn-gold" type="submit">Reset Password</button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </>
      )
    }

    if (activePage === 'students') {
      return (
        <>
          <div className="card">
            <div className="card-hdr"><div className="card-title">Student Lookup</div></div>
            <form className="admin-form" onSubmit={handleSearchStudent}>
              <div className="fgroup" style={{ flex: 1 }}>
                <label>Student ID</label>
                <input value={studentId} onChange={(event) => setStudentId(event.target.value)} placeholder="Student ID" />
              </div>
              <button className="btn btn-gold" type="submit">Search</button>
            </form>
          </div>
          {student && (
            <div className="card">
              <div className="card-hdr"><div className="card-title">Student Detail</div></div>
              <p><strong>Name:</strong> {student.full_name || student.name || '—'}</p>
              <p><strong>ID:</strong> {student.student_number || student.user_id || student.student_id || '—'}</p>
              <p><strong>Email:</strong> {student.email || '—'}</p>
              <p><strong>Status:</strong> {student.status || 'Active'}</p>
            </div>
          )}
        </>
      )
    }

    if (activePage === 'account') {
      return (
        <div className="card">
          <div className="card-hdr"><div className="card-title">Change Password</div></div>
          <form className="admin-form" onSubmit={handleChangePassword}>
            <div className="frow">
              <div className="fgroup"><label>Current password</label><input type="password" value={passwordForm.old_password} onChange={(event) => { setPasswordForm({ ...passwordForm, old_password: event.target.value }); setPasswordError('') }} placeholder="Current password" /></div>
              <div className="fgroup"><label>New password</label><input type="password" value={passwordForm.new_password} onChange={(event) => { setPasswordForm({ ...passwordForm, new_password: event.target.value }); setPasswordError('') }} placeholder="New password" /></div>
            </div>
            <button className="btn btn-gold" type="submit">Save password</button>
            {passwordError && <div className="password-error">{passwordError}</div>}
          </form>
        </div>
      )
    }

    return null
  }

  return (
    <div className="admin-dashboard-app">
      <div className="sidebar">
        <div className="logo">
          <div className="logo-icon"><BookOpen size={27} strokeWidth={1.9} aria-hidden="true" /></div>
          <div className="logo-text">
            <div className="logo-title">LIBRASYS</div>
            <div className="logo-sub">Administrator</div>
          </div>
        </div>
        <nav className="nav">
          {navSections.map((section) => (
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
      {showPasswordSuccessModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 2000 }}>
          <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: '12px', padding: '24px', maxWidth: '420px', width: '100%', color: 'var(--text)' }}>
            <div style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px' }}>Password Updated</div>
            <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '24px' }}>Your password has been changed successfully.</div>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button onClick={handlePasswordSuccessConfirm} className="btn btn-primary" type="button">OK</button>
            </div>
          </div>
        </div>
      )}
      <div className="main">
        <div className="topbar">
          <div className="page-title">{pageTitles[activePage] || 'Overview'}</div>
          <div className="search-wrap">
            <input
              className="search-input"
              value={searchQuery}
              onChange={(event) => {
                setSearchQuery(event.target.value)
                setBookInventoryPage(1)
              }}
              placeholder="Search..."
            />
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
                    notifications.map((notif) => (
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
            <div className="topbar-user-profile">
              <div className="avatar">AD</div>
              <div className="topbar-user-text">
                <div className="topbar-user-name">Admin User</div>
                <div className="topbar-user-email">{adminEmail}</div>
              </div>
            </div>
            <button className="topbar-logout-button" type="button" title="Logout" onClick={() => setShowLogoutConfirm(true)} aria-label="Logout">
              <LogOut size={17} aria-hidden="true" />
            </button>
          </div>
        </div>
        <div className="content">
          {renderPage()}
        </div>
      </div>
    </div>
  )
}

