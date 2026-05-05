import { useEffect, useMemo, useState } from 'react'
import { formatCurrency } from '../../shared/utils/index.js'
import { searchActiveLoans, returnLoan } from './returnService.js'

export function ReturnPlatform({ onLoanReturned }) {
  const [searchQuery, setSearchQuery] = useState('')
  const [loans, setLoans] = useState([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [returningLoanId, setReturningLoanId] = useState(null)

  const loadLoans = async (query = '') => {
    setError('')
    setMessage('')
    setLoading(true)
    try {
      const results = await searchActiveLoans(query)
      setLoans(Array.isArray(results) ? results : [])
      if (!results || results.length === 0) {
        setMessage(query ? 'No active loans matched your search.' : 'No active loans available for return.')
      }
    } catch (err) {
      setError(err?.response?.data?.message || err?.message || 'Unable to load active loans.')
      setLoans([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadLoans('')
  }, [])

  const handleSearch = async (event) => {
    event.preventDefault()
    await loadLoans(searchQuery)
  }

  const handleReset = async () => {
    setSearchQuery('')
    await loadLoans('')
  }

  const handleReturn = async (loanId) => {
    const confirmed = window.confirm(
      `Return loan #${loanId}? This will mark the loan as returned, update availability, and process any reservation queue.`
    )
    if (!confirmed) {
      return
    }

    setReturningLoanId(loanId)
    setError('')
    setMessage('')

    try {
      await returnLoan(loanId)
      setMessage(`Loan #${loanId} returned successfully.`)
      if (typeof onLoanReturned === 'function') {
        await onLoanReturned()
      }
      await loadLoans(searchQuery)
    } catch (err) {
      setError(err?.response?.data?.message || err?.message || 'Failed to return loan.')
    } finally {
      setReturningLoanId(null)
    }
  }

  const filteredLoans = useMemo(() => {
    if (!searchQuery.trim() || loading) {
      return loans
    }

    const normalized = searchQuery.trim().toLowerCase()
    return loans.filter((loan) => {
      const values = [
        String(loan.loan_id || ''),
        String(loan.student_id || loan.user_id || ''),
        String(loan.student_name || ''),
        String(loan.student_number || ''),
        String(loan.student_email || ''),
        String(loan.book_title || ''),
        String(loan.isbn || ''),
        String(loan.copy_code || ''),
        String(loan.barcode_value || ''),
        String(loan.qr_token || ''),
      ]
      return values.some((value) => value.toLowerCase().includes(normalized))
    })
  }, [loans, searchQuery, loading])

  const displayLoans = filteredLoans

  return (
    <div className="card">
      <div className="card-hdr">
        <div>
          <div className="card-title">Centralized Return Platform</div>
          <div className="card-subtitle">Search active loans by student, book, ISBN, barcode/QR, or loan ID.</div>
        </div>
      </div>

      <div className="card-body">
        <form className="search-form" onSubmit={handleSearch}>
          <input
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search loans by student, book title, ISBN, barcode, or loan ID"
            className="search-input"
          />
          <button className="btn btn-gold" type="submit" disabled={loading}>Search</button>
          <button className="btn btn-outline" type="button" onClick={handleReset} disabled={loading}>Reset</button>
        </form>

        {error && <div className="alert alert-error">{error}</div>}
        {!error && message && <div className="alert alert-info">{message}</div>}

        {loading ? (
          <div className="card-body">Loading loans...</div>
        ) : (
          <div className="admin-table-container">
            <table>
              <thead>
                <tr>
                  <th>Loan</th>
                  <th>Book</th>
                  <th>ISBN</th>
                  <th>Copy</th>
                  <th>Student</th>
                  <th>Borrowed</th>
                  <th>Due</th>
                  <th>Overdue</th>
                  <th>Fine</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {displayLoans.length === 0 ? (
                  <tr>
                    <td colSpan="11" className="empty-cell">No loans available for return.</td>
                  </tr>
                ) : (
                  displayLoans.map((loan) => (
                    <tr key={loan.loan_id}>
                      <td>{loan.loan_id}</td>
                      <td>{loan.book_title || loan.book_id}</td>
                      <td>{loan.isbn || '—'}</td>
                      <td>{loan.copy_code || loan.barcode_value || loan.qr_token || '—'}</td>
                      <td>
                        <div className="loan-student-cell">
                          <strong>{loan.student_name || loan.student_number || loan.student_id || loan.user_id}</strong>
                          {(loan.student_email || loan.student_number) && (
                            <span>{loan.student_email || loan.student_number}</span>
                          )}
                        </div>
                      </td>
                      <td>{loan.borrowed_at || loan.issue_date || '—'}</td>
                      <td>{loan.due_date || '—'}</td>
                      <td>{loan.days_overdue || 0}</td>
                      <td>{formatCurrency(loan.fine_amount)}</td>
                      <td>{loan.status || (loan.returned ? 'Returned' : 'Active')}</td>
                      <td>
                        <button
                          className="btn btn-gold btn-sm"
                          type="button"
                          disabled={returningLoanId === loan.loan_id}
                          onClick={() => handleReturn(loan.loan_id)}
                        >
                          {returningLoanId === loan.loan_id ? 'Returning...' : 'Return'}
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
