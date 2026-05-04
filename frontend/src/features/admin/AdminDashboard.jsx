import { useEffect, useMemo, useState } from 'react'
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
  fetchLoans,
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

const pageTitles = {
  overview: 'Overview',
  registrations: 'Registration Requests',
  books: 'Books',
  loans: 'Issue / Return',
  students: 'Students',
  categories: 'Categories',
  authors: 'Authors',
  account: 'Change Password'
}

export function AdminDashboard() {
  const navigate = useNavigate()
  const [activePage, setActivePage] = useState('overview')
  const [categories, setCategories] = useState([])
  const [authors, setAuthors] = useState([])
  const [books, setBooks] = useState([])
  const [loans, setLoans] = useState([])
  const [studentId, setStudentId] = useState('')
  const [student, setStudent] = useState(null)
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

  useEffect(() => {
    loadCategories()
    loadAuthors()
    loadBooks()
    loadLoans()
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

  const stats = useMemo(
    () => [
      { label: 'Categories', value: categories.length, type: 'gold' },
      { label: 'Authors', value: authors.length, type: 'blue' },
      { label: 'Books', value: books.length, type: 'green' },
      { label: 'Loans', value: loans.length, type: 'purple' }
    ],
    [categories, authors, books, loans]
  )

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
      setMessage('No document available for this request.')
      return
    }

    try {
      const blob = await fetchRegistrationDocument(documentUrl)
      const objectUrl = URL.createObjectURL(blob)
      window.open(objectUrl, '_blank', 'noopener noreferrer')
      setTimeout(() => URL.revokeObjectURL(objectUrl), 10000)
    } catch {
      setMessage('Unable to load registration document.')
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
            <div className="card-title">Registration Requests</div>
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
                {registrationRequests.map((request) => (
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
            <div className="card-title">Category Management</div>
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
                {categories.map((category) => (
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
            <div className="card-title">Author Management</div>
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
                {authors.map((author) => (
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
            </div>
            <div className="admin-table-container">
              <table>
                <thead>
                  <tr><th>Title</th><th>Author</th><th>ISBN</th><th>Available</th></tr>
                </thead>
                <tbody>
                  {books.map((book) => (
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
            <div className="card-hdr"><div className="card-title">Current Loans</div></div>
            <div className="admin-table-container">
              <table>
                <thead>
                  <tr><th>Loan ID</th><th>Book</th><th>Student</th><th>Status</th></tr>
                </thead>
                <tbody>
                  {loans.map((loan) => (
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
          <div className="logo-icon">📚</div>
          <div className="logo-title">LIBRASYS</div>
          <div className="logo-sub">Administrator</div>
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
        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="avatar">AD</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '12px', color: 'var(--text)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>Admin User</div>
              <div style={{ fontSize: '10px', color: 'var(--muted)' }}>admin@librasys.edu</div>
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
            <input className="search-input" value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder="Search..." />
          </div>
          <span style={{ fontSize: '18px', cursor: 'pointer' }}>🔔</span>
          <div className="avatar">AD</div>
        </div>
        <div className="content">
          {renderPage()}
        </div>
      </div>
    </div>
  )
}

