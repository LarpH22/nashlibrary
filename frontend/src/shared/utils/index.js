export function formatCurrency(amount) {
  return amount.toLocaleString(undefined, { style: 'currency', currency: 'USD' })
}

export function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString()
}
