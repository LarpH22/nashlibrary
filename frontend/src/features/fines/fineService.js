import api from '../../shared/api.js'

export async function calculateFine(loanId) {
  const response = await api.get('/api/fines/calculate', { params: { loan_id: loanId } })
  return response.data
}

export async function payFine(loanId, paymentMethod = 'online') {
  const response = await api.post('/api/fines/pay', { loan_id: loanId, payment_method: paymentMethod })
  return response.data
}

export async function previewFinePayment(loanId, paymentMethod = 'online') {
  const response = await api.post('/api/fines/payment-preview', { loan_id: loanId, payment_method: paymentMethod })
  return response.data
}

export async function confirmFinePayment(loanId, paymentMethod = 'online', paymentReference = '') {
  const response = await api.post('/api/fines/pay', {
    loan_id: loanId,
    payment_method: paymentMethod,
    payment_reference: paymentReference
  })
  return response.data
}

export async function reviewFinePayment(fineId, action) {
  const response = await api.patch(`/api/fines/${fineId}/payment`, { action })
  return response.data
}

export async function fetchStudentFines() {
  const response = await api.get('/api/fines/student')
  return response.data
}
