import { useState, useEffect } from 'react'
import axios from 'axios'

const FinesCard = ({ token }) => {
  const [fines, setFines] = useState({
    total_pending: 0,
    total_paid: 0,
    fines: []
  })
  const [showDetails, setShowDetails] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchFines = async () => {
      try {
        setLoading(true)
        setError(null)

        const authToken =
          token ||
          axios.defaults.headers.common['Authorization']?.replace(/^Bearer\s+/, '') ||
          localStorage.getItem('token') ||
          localStorage.getItem('access_token')

        if (!authToken) {
          setError('No authentication token')
          return
        }

        const response = await axios.get('/student/fines', {
          headers: {
            Authorization: `Bearer ${authToken}`
          }
        })

        setFines(response.data)
      } catch (error) {
        console.error('Error fetching fines:', error)
        setError(error.response?.data?.message || error.message || 'Failed to load fines')
      } finally {
        setLoading(false)
      }
    }

    fetchFines()
  }, [token])

  if (loading) {
    return (
      <div className="fines-card">
        <p>Loading fines...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="fines-card">
        <p className="fines-error">Error loading fines: {error}</p>
      </div>
    )
  }

  const hasPending = fines.total_pending > 0

  return (
    <div className={`fines-card ${hasPending ? 'pending' : 'paid'}`}>
      <div className="fines-header">
        <div>
          <h4>Account Fines</h4>
          <p className="fines-status">{hasPending ? 'Outstanding' : 'All Paid'}</p>
        </div>
        <div className="fines-amount">${fines.total_pending.toFixed(2)}</div>
      </div>

      {!hasPending && (
        <p className="fines-checkline">✓ No outstanding balance</p>
      )}

      {hasPending && (
        <p className="fines-warning">⚠️ You have outstanding fines. Please settle them to avoid service restrictions.</p>
      )}

      {fines.total_paid > 0 && (
        <p className="fines-paid">Paid: ${fines.total_paid.toFixed(2)}</p>
      )}

      {fines.fines && fines.fines.length > 0 && (
        <>
          <button type="button" className="view-details-btn" onClick={() => setShowDetails(!showDetails)}>
            {showDetails ? 'Hide Details' : 'View Details'} ({fines.fines.length})
          </button>

          {showDetails && (
            <div className="fines-details">
              {fines.fines.map((fine) => (
                <div key={fine.fine_id} className="fine-item">
                  <div className="fine-left">
                    <div className="fine-book">{fine.book_title || 'Unknown Book'}</div>
                    <div className="fine-reason">{fine.reason || 'Overdue fine'}</div>
                  </div>
                  <div className="fine-right">
                    <div className="fine-amount">${fine.amount.toFixed(2)}</div>
                    <div className={`fine-badge fine-badge-${fine.status}`}>{fine.status.charAt(0).toUpperCase() + fine.status.slice(1)}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {(!fines.fines || fines.fines.length === 0) && !hasPending && (
        <p className="fines-no-records">✅ No fines on your account.</p>
      )}
    </div>
  )
}

export default FinesCard
