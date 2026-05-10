import api from '../../shared/api.js'

export async function fetchRegistrationRequests({ page, limit } = {}) {
  const response = await api.get('/api/admin/registration-requests', { params: { page, limit } })
  return response.data
}

export async function approveRegistration(requestId) {
  const response = await api.post('/api/auth/approve-registration', { request_id: requestId })
  return response.data
}

export async function fetchRegistrationDocument(url) {
  const response = await api.get(url, { responseType: 'blob' })
  return response.data
}

export async function rejectRegistration(requestId) {
  const response = await api.post('/api/admin/reject-registration', { request_id: requestId })
  return response.data
}

export async function fetchCategories({ page, limit, search } = {}) {
  const response = await api.get('/api/admin/categories', { params: { page, limit, search } })
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

export async function fetchAuthors({ page, limit, search } = {}) {
  const response = await api.get('/api/admin/authors', { params: { page, limit, search } })
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

export async function borrowBook(bookId, studentNumber) {
  const response = await api.post('/api/admin/loans', { book_id: bookId, student_number: studentNumber })
  return response.data
}

export async function returnBook(loanId) {
  const response = await api.post('/books/return', { loan_id: loanId })
  return response.data
}

export async function fetchStudent(studentId) {
  const response = await api.get(`/api/admin/students/${encodeURIComponent(studentId)}`)
  return response.data
}

export async function fetchStudents({ page, limit } = {}) {
  const response = await api.get('/api/admin/students', { params: { page, limit } })
  return response.data
}

export async function updateStudent(studentId, student) {
  const response = await api.put(`/api/admin/students/${encodeURIComponent(studentId)}`, student)
  return response.data
}

export async function resetStudentPassword(studentId, newPassword, confirmPassword) {
  const response = await api.post(`/api/admin/students/${encodeURIComponent(studentId)}/reset-password`, { new_password: newPassword, confirm_password: confirmPassword })
  return response.data
}

export async function fetchLoans({ page, limit, status, search } = {}) {
  const response = await api.get('/api/admin/loans', { params: { page, limit, status, search } })
  return response.data
}

export async function fetchAdminFines({ page, limit } = {}) {
  const response = await api.get('/api/fines/admin', { params: { page, limit } })
  return response.data
}

export async function updateFineStatus(fineId, status) {
  const response = await api.patch(`/api/fines/${fineId}/status`, { status })
  return response.data
}

export async function reviewFinePayment(fineId, action) {
  const response = await api.patch(`/api/fines/${fineId}/payment`, { action })
  return response.data
}

export async function fetchFineReceipt(fineId) {
  const response = await api.get(`/api/fines/${fineId}/receipt`, { responseType: 'blob' })
  return response.data
}

export async function changePassword(oldPassword, newPassword, confirmPassword) {
  const response = await api.post('/api/admin/password', { old_password: oldPassword, new_password: newPassword, confirm_password: confirmPassword })
  return response.data
}
