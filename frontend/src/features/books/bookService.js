import api from '../../shared/api.js'

export async function fetchBooks() {
  const response = await api.get('/books')
  return response.data
}

export async function searchBooks(filters) {
  const response = await api.get('/api/books/search', { params: filters })
  return response.data
}

export async function borrowBook(loanRequest) {
  const response = await api.post('/books/borrow', loanRequest)
  return response.data
}

export async function returnBook(loanId) {
  const response = await api.post('/books/return', { loan_id: loanId })
  return response.data
}
