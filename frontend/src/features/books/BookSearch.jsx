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
  const activeBorrowedIds = useMemo(() => new Set(borrowedBookIds.map((id) => Number(id))), [borrowedBookIds])

  const categories = useMemo(() => {
    const setValues = new Set(books.map((book) => book.category).filter(Boolean))
    return ['Fiction', 'Non-Fiction', 'Sci-Fi', 'History', 'Biography', 'Children', 'Math', 'Technology']
      .concat([...setValues].filter((value) => !['Fiction', 'Non-Fiction', 'Sci-Fi', 'History', 'Biography', 'Children', 'Math', 'Technology'].includes(value)))
  }, [books])

  const currentFilters = () => ({ title, author, category, isbn, availability, history })

  const loadBooks = async (filters = currentFilters()) => {
    setLoading(true)
    setError('')
    try {
      const response = await searchBooks(filters)
      setBooks(response.books || [])
    } catch (err) {
      setError('Unable to load book results. Please try again.')
      setBooks([])
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
    await loadBooks()
  }

  const clearFilters = async () => {
    setTitle('')
    setAuthor('')
    setCategory('')
    setIsbn('')
    setAvailability('')
    setHistory('')
    await loadBooks(emptyFilters)
  }

  const handleBorrow = async (book) => {
    setError('')
    setBorrowingId(book.book_id)
    try {
      await borrowBook({ book_id: book.book_id })
      await loadBooks()
      if (onBorrowed) {
        await onBorrowed(book)
      }
    } catch (err) {
      const message = err?.response?.data?.message || 'Unable to borrow this book. Please try again.'
      await loadBooks()
      setError(message)
    } finally {
      setBorrowingId(null)
    }
  }

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
          <div style={{ color: 'var(--muted)', fontSize: '13px' }}>{books.length} results</div>
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
                          {unavailable ? 'Unavailable' : alreadyBorrowed ? 'Borrowed' : borrowingId === book.book_id ? 'Borrowing...' : 'Borrow'}
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
    </div>
  )
}
