import api from '../../shared/api.js'

export async function fetchRegistrationRequests() {
  const response = await api.get('/api/admin/registration-requests')
  return response.data
}

export async function approveRegistration(requestId) {
  const response = await api.post('/api/auth/approve-registration', { request_id: requestId })
  return response.data
}

export async function rejectRegistration(requestId) {
  const response = await api.post('/api/admin/reject-registration', { request_id: requestId })
  return response.data
}

export async function fetchCategories() {
  const response = await api.get('/api/admin/categories')
  return response.data
}

export async function createCategory(name) {
  const response = await api.post('/api/admin/categories', { name })
  return response.data
}

export async function deleteCategory(categoryId) {
  const response = await api.delete(`/api/admin/categories/${categoryId}`)
  return response.data
}

export async function fetchAuthors() {
  const response = await api.get('/api/admin/authors')
  return response.data
}

export async function createAuthor(name) {
  const response = await api.post('/api/admin/authors', { name })
  return response.data
}

export async function deleteAuthor(authorId) {
  const response = await api.delete(`/api/admin/authors/${authorId}`)
  return response.data
}

export async function fetchBooks() {
  const response = await api.get('/books/')
  return response.data
}

export async function createBook(book) {
  const response = await api.post('/books/', book)
  return response.data
}

export async function borrowBook(bookId, userId) {
  const response = await api.post('/books/borrow', { book_id: bookId, user_id: userId })
  return response.data
}

export async function returnBook(loanId) {
  const response = await api.post('/books/return', { loan_id: loanId })
  return response.data
}

export async function fetchStudent(studentId) {
  const response = await api.get(`/api/admin/students/${studentId}`)
  return response.data
}

export async function fetchLoans() {
  const response = await api.get('/api/admin/loans')
  return response.data
}

export async function changePassword(oldPassword, newPassword) {
  const response = await api.post('/api/admin/password', { old_password: oldPassword, new_password: newPassword })
  return response.data
}
