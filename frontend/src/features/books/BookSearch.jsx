import { useEffect, useMemo, useState } from 'react'
import { searchBooks } from './bookService.js'

const availabilityOptions = [
  { value: '', label: 'All' },
  { value: 'available', label: 'Available' },
  { value: 'borrowed', label: 'Borrowed' }
]

export function BookSearch({ initialKeyword = '' }) {
  const [title, setTitle] = useState(initialKeyword)
  const [author, setAuthor] = useState('')
  const [category, setCategory] = useState('')
  const [isbn, setIsbn] = useState('')
  const [availability, setAvailability] = useState('')
  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const categories = useMemo(() => {
    const setValues = new Set(books.map((book) => book.category).filter(Boolean))
    return ['Fiction', 'Non-Fiction', 'Sci-Fi', 'History', 'Biography', 'Children', 'Math', 'Technology']
      .concat([...setValues].filter((value) => !['Fiction', 'Non-Fiction', 'Sci-Fi', 'History', 'Biography', 'Children', 'Math', 'Technology'].includes(value)))
  }, [books])

  const loadBooks = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await searchBooks({ title, author, category, isbn, availability })
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

  const clearFilters = () => {
    setTitle('')
    setAuthor('')
    setCategory('')
    setIsbn('')
    setAvailability('')
  }

  return (
    <div className="card">
      <div className="card-hdr"><div className="card-title">Search Library Catalog</div></div>
      <form className="admin-form" onSubmit={handleSubmit} style={{ flexDirection: 'column', gap: '16px' }}>
        <div className="frow">
          <div className="fgroup">
            <label>Search by title</label>
            <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Keyword, title, or phrase" />
          </div>
          <div className="fgroup">
            <label>Filter by author</label>
            <input value={author} onChange={(event) => setAuthor(event.target.value)} placeholder="Author name" />
          </div>
        </div>
        <div className="frow">
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
        </div>
        <div className="frow">
          <div className="fgroup" style={{ flex: 1 }}>
            <label>ISBN</label>
            <input value={isbn} onChange={(event) => setIsbn(event.target.value)} placeholder="ISBN number" />
          </div>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
            <button className="btn btn-green" type="submit">Search</button>
            <button className="btn btn-outline" type="button" onClick={clearFilters}>Reset</button>
          </div>
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
              </tr>
            </thead>
            <tbody>
              {books.length === 0 ? (
                <tr><td colSpan="5" style={{ color: 'var(--muted)', padding: '18px', textAlign: 'center' }}>No books found. Update the filters and try again.</td></tr>
              ) : (
                books.map((book) => (
                  <tr key={book.book_id || book.id}>
                    <td>{book.title}</td>
                    <td>{book.author}</td>
                    <td>{book.category || 'Uncategorized'}</td>
                    <td>{book.isbn}</td>
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
    </div>
  )
}
