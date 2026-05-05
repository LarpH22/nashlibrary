import api from '../../shared/api.js'

export async function reserveBook(bookId) {
  const response = await api.post('/api/reservations/', { book_id: bookId })
  return response.data
}

export async function fetchStudentReservations({ page, limit } = {}) {
  const response = await api.get('/api/reservations/student', {
    params: { page, limit }
  })
  return response.data
}

export async function cancelStudentReservation(reservationId) {
  const response = await api.delete(`/api/reservations/${reservationId}`)
  return response.data
}

export async function fetchReservations(status = '', { page, limit } = {}) {
  const params = { ...(status ? { status } : {}), page, limit }
  const response = await api.get('/api/reservations/', { params })
  return response.data
}

export async function approveReservation(reservationId) {
  const response = await api.post(`/api/reservations/${reservationId}/approve`)
  return response.data
}

export async function cancelReservation(reservationId) {
  const response = await api.post(`/api/reservations/${reservationId}/cancel`)
  return response.data
}

export async function claimReservation(reservationId) {
  const response = await api.post(`/api/reservations/${reservationId}/claim`)
  return response.data
}

export async function expireReservations() {
  const response = await api.post('/api/reservations/expire')
  return response.data
}
