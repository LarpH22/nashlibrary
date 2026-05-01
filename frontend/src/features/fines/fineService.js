import api from '../../shared/api.js'

export async function calculateFine(loanId) {
  const response = await api.get('/fines/calculate', { params: { loan_id: loanId } })
  return response.data
}

export async function payFine(loanId) {
  const response = await api.post('/fines/pay', { loan_id: loanId })
  return response.data
}
