export function formatCurrency(amount) {
  return Number(amount || 0).toLocaleString('en-PH', { style: 'currency', currency: 'PHP' })
}

export function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString()
}
