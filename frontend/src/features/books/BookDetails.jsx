export function BookDetails({ book }) {
  if (!book) {
    return <div>No book selected.</div>
  }

  return (
    <article className="book-details">
      <h3>{book.title}</h3>
      <p>Author: {book.author}</p>
      <p>ISBN: {book.isbn}</p>
      <p>Status: {book.status}</p>
      <p>Available copies: {book.available_copies}</p>
    </article>
  )
}
