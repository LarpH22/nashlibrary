import { useEffect, useState } from 'react'
import { fetchBooks, borrowBook } from './bookService.js'

export function BookList() {
  const [books, setBooks] = useState([])
  const [message, setMessage] = useState('')

  useEffect(() => {
    fetchBooks().then(setBooks).catch(() => setMessage('Unable to load books'))
  }, [])

  const handleBorrow = async (bookId) => {
    try {
      const data = await borrowBook({ book_id: bookId, user_id: 1 })
      setMessage(data.message)
    } catch (error) {
      setMessage('Unable to borrow book')
    }
  }

  return (
    <section className="book-list">
      <h2>Available Books</h2>
      {message && <div className="message">{message}</div>}
      <ul>
        {books.map((book) => (
          <li key={book.book_id || book.id}>
            <strong>{book.title}</strong> by {book.author}
            <div>{book.status || 'available'}</div>
            <button onClick={() => handleBorrow(book.book_id || book.id)}>Borrow</button>
          </li>
        ))}
      </ul>
    </section>
  )
}
