import api from '../../shared/api.js'

export async function searchActiveLoans(search = '') {
  const params = { status: 'active' }
  const query = String(search || '').trim()
  if (query) {
    params.search = query
  }

  const response = await api.get('/api/admin/loans', { params })
  return response.data
}

export async function returnLoan(loanId) {
  const response = await api.post('/books/return', { loan_id: Number(loanId) })
  return response.data
}
