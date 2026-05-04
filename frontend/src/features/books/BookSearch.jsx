import { useEffect, useMemo, useState } from 'react'
import { borrowBook, searchBooks } from './bookService.js'

const availabilityOptions = [
  { value: '', label: 'All' },
  { value: 'available', label: 'Available' },
  { value: 'borrowed', label: 'Borrowed' },
  { value: 'unavailable', label: 'Out of Stock' },
  { value: 'maintenance', label: 'Maintenance' },
  { value: 'lost', label: 'Lost' }
]

const historyOptions = [
  { value: '', label: 'All history' },
  { value: 'borrowed', label: 'Currently borrowed' },
  { value: 'returned', label: 'Returned before' },
  { value: 'any', label: 'Has history' },
  { value: 'none', label: 'No history' }
]

const emptyFilters = {
  title: '',
  author: '',
  category: '',
  isbn: '',
  availability: '',
  history: ''
}

const pageSize = 10

const buildPageItems = (currentPage, totalPages) => {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1)
  }

  const pages = new Set([1, totalPages, currentPage, currentPage - 1, currentPage + 1])
  if (currentPage <= 3) {
    pages.add(2)
    pages.add(3)
    pages.add(4)
  }
  if (currentPage >= totalPages - 2) {
    pages.add(totalPages - 1)
    pages.add(totalPages - 2)
    pages.add(totalPages - 3)
  }

  const sorted = [...pages].filter((page) => page >= 1 && page <= totalPages).sort((a, b) => a - b)
  return sorted.reduce((items, page) => {
    const previous = items[items.length - 1]
    if (typeof previous === 'number' && page - previous > 1) {
      items.push(`ellipsis-${previous}-${page}`)
    }
    items.push(page)
    return items
  }, [])
}

export function BookSearch({ initialKeyword = '', borrowedBookIds = [], onBorrowed }) {
  const [title, setTitle] = useState(initialKeyword)
  const [author, setAuthor] = useState('')
  const [category, setCategory] = useState('')
  const [isbn, setIsbn] = useState('')
  const [availability, setAvailability] = useState('')
  const [history, setHistory] = useState('')
  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(false)
  const [borrowingId, setBorrowingId] = useState(null)
  const [error, setError] = useState('')
  const [pagination, setPagination] = useState({
    page: 1,
    limit: pageSize,
    total: 0,
    total_pages: 1
  })
  const activeBorrowedIds = useMemo(() => new Set(borrowedBookIds.map((id) => Number(id))), [borrowedBookIds])

  const categories = useMemo(() => {
    const setValues = new Set(books.map((book) => book.category).filter(Boolean))
    return ['Fiction', 'Non-Fiction', 'Sci-Fi', 'History', 'Biography', 'Children', 'Math', 'Technology']
      .concat([...setValues].filter((value) => !['Fiction', 'Non-Fiction', 'Sci-Fi', 'History', 'Biography', 'Children', 'Math', 'Technology'].includes(value)))
  }, [books])

  const currentFilters = () => ({ title, author, category, isbn, availability, history })

  const loadBooks = async (filters = currentFilters(), page = 1) => {
    setLoading(true)
    setError('')
    try {
      const response = await searchBooks({ ...filters, page, limit: pageSize })
      setBooks(response.books || [])
      setPagination(response.pagination || {
        page,
        limit: pageSize,
        total: response.books?.length || 0,
        total_pages: 1
      })
    } catch (err) {
      setError('Unable to load book results. Please try again.')
      setBooks([])
      setPagination({ page: 1, limit: pageSize, total: 0, total_pages: 1 })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    setTitle(initialKeyword || '')
  }, [initialKeyword])

  useEffect(() => {
    loadBooks()
  }, [])

  const handleSubmit = async (event) => {
    event.preventDefault()
    await loadBooks(currentFilters(), 1)
  }

  const clearFilters = async () => {
    setTitle('')
    setAuthor('')
    setCategory('')
    setIsbn('')
    setAvailability('')
    setHistory('')
    await loadBooks(emptyFilters, 1)
  }

  const goToPage = async (page) => {
    const totalPages = pagination.total_pages || 1
    const nextPage = Math.min(Math.max(page, 1), totalPages)
    if (nextPage === pagination.page || loading) {
      return
    }
    await loadBooks(currentFilters(), nextPage)
  }

  const handleBorrow = async (book) => {
    setError('')
    setBorrowingId(book.book_id)
    try {
      await borrowBook({ book_id: book.book_id })
      await loadBooks(currentFilters(), pagination.page)
      if (onBorrowed) {
        await onBorrowed(book)
      }
    } catch (err) {
      const message = err?.response?.data?.message || 'Unable to request this book. Please try again.'
      await loadBooks(currentFilters(), pagination.page)
      setError(message)
    } finally {
      setBorrowingId(null)
    }
  }

  const totalPages = pagination.total_pages || 1
  const pageItems = buildPageItems(pagination.page || 1, totalPages)
  const firstResult = pagination.total === 0 ? 0 : ((pagination.page - 1) * pagination.limit) + 1
  const lastResult = Math.min(pagination.page * pagination.limit, pagination.total)

  return (
    <div className="card">
      <div className="card-hdr"><div className="card-title">Search Library Catalog</div></div>
      <form className="catalog-search-form" onSubmit={handleSubmit}>
        <div className="catalog-filter-grid">
          <div className="fgroup">
            <label>Search by title</label>
            <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Keyword, title, or phrase" />
          </div>
          <div className="fgroup">
            <label>Filter by author</label>
            <input value={author} onChange={(event) => setAuthor(event.target.value)} placeholder="Author name" />
          </div>
          <div className="fgroup">
            <label>Category</label>
            <select value={category} onChange={(event) => setCategory(event.target.value)}>
              <option value="">All categories</option>
              {categories.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </div>
          <div className="fgroup">
            <label>Availability</label>
            <select value={availability} onChange={(event) => setAvailability(event.target.value)}>
              {availabilityOptions.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
          <div className="fgroup">
            <label>ISBN</label>
            <input value={isbn} onChange={(event) => setIsbn(event.target.value)} placeholder="ISBN number" />
          </div>
          <div className="fgroup">
            <label>History</label>
            <select value={history} onChange={(event) => setHistory(event.target.value)}>
              {historyOptions.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="catalog-filter-actions">
          <button className="btn btn-green" type="submit">Search</button>
          <button className="btn btn-outline" type="button" onClick={clearFilters}>Reset</button>
        </div>
      </form>
      <div style={{ marginTop: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <div style={{ color: 'var(--muted)', fontSize: '13px' }}>
            {pagination.total > 0 ? `${firstResult}-${lastResult} of ${pagination.total} results` : '0 results'}
          </div>
          {loading && <div style={{ color: 'var(--green)', fontSize: '13px' }}>Loading books...</div>}
        </div>
        {error && <div className="card" style={{ borderColor: 'var(--red)', color: 'var(--red)' }}>{error}</div>}
        <div className="admin-table-container">
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Author</th>
                <th>Category</th>
                <th>ISBN</th>
                <th>Availability</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {books.length === 0 ? (
                <tr><td colSpan="6" style={{ color: 'var(--muted)', padding: '18px', textAlign: 'center' }}>No books found. Update the filters and try again.</td></tr>
              ) : (
                books.map((book) => {
                  const unavailable = book.status !== 'available' || book.available_copies === 0
                  const alreadyBorrowed = activeBorrowedIds.has(Number(book.book_id))
                  const availabilityLabel = book.status === 'available'
                    ? 'Available'
                    : book.status === 'borrowed'
                      ? 'Borrowed'
                      : book.status === 'maintenance'
                        ? 'Maintenance'
                        : book.status === 'lost'
                          ? 'Lost'
                          : 'Out of Stock'
                  return (
                    <tr key={book.book_id || book.id}>
                      <td>{book.title}</td>
                      <td>{book.author}</td>
                      <td>{book.category || 'Uncategorized'}</td>
                      <td>{book.isbn}</td>
                      <td style={{ color: unavailable ? 'var(--red)' : 'var(--green)' }}>
                        {availabilityLabel}
                      </td>
                      <td>
                        <button
                          className="btn btn-green btn-sm"
                          type="button"
                          disabled={loading || unavailable || alreadyBorrowed || borrowingId === book.book_id}
                          onClick={() => handleBorrow(book)}
                        >
                          {unavailable ? 'Unavailable' : alreadyBorrowed ? 'Requested' : borrowingId === book.book_id ? 'Requesting...' : 'Request'}
                        </button>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
        {totalPages > 1 && (
          <nav className="catalog-pagination" aria-label="Book catalog pagination">
            <button
              className="catalog-page-button catalog-page-arrow"
              type="button"
              disabled={loading || pagination.page <= 1}
              onClick={() => goToPage(pagination.page - 1)}
            >
              Previous
            </button>
            <div className="catalog-page-numbers">
              {pageItems.map((item) => (
                typeof item === 'number' ? (
                  <button
                    key={item}
                    className={`catalog-page-button ${item === pagination.page ? 'active' : ''}`}
                    type="button"
                    disabled={loading}
                    aria-current={item === pagination.page ? 'page' : undefined}
                    onClick={() => goToPage(item)}
                  >
                    {item}
                  </button>
                ) : (
                  <span key={item} className="catalog-page-ellipsis">...</span>
                )
              ))}
            </div>
            <button
              className="catalog-page-button catalog-page-arrow"
              type="button"
              disabled={loading || pagination.page >= totalPages}
              onClick={() => goToPage(pagination.page + 1)}
            >
              Next
            </button>
          </nav>
        )}
      </div>
    </div>
  )
}
