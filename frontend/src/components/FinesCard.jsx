import React, { useState, useEffect } from 'react';

export const FinesCard = ({ token }) => {
  const [fines, setFines] = useState({
    total_pending: 0,
    total_paid: 0,
    fines: []
  });
  const [showDetails, setShowDetails] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchFines = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const authToken = token || localStorage.getItem('access_token');
        if (!authToken) {
          setError('No authentication token');
          setLoading(false);
          return;
        }

        const response = await fetch('http://127.0.0.1:5000/student/fines', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch fines: ${response.status}`);
        }

        const data = await response.json();
        setFines(data);
      } catch (error) {
        console.error('Error fetching fines:', error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchFines();
  }, [token]);

  if (loading) {
    return (
      <div className="fines-card" style={{ borderLeftColor: '#94a3b8' }}>
        <p>Loading fines...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fines-card" style={{ borderLeftColor: '#94a3b8' }}>
        <p style={{ color: '#cbd5e1' }}>Error loading fines: {error}</p>
      </div>
    );
  }

  // Show card even if no fines (for display purposes)
  const hasPending = fines.total_pending > 0;
  const statusColor = hasPending ? '#e51c1c' : '#22c55e'; // Red for pending, Green for all paid

  return (
    <div className="fines-card" style={{ borderLeftColor: statusColor }}>
      <div className="fines-header">
        <div>
          <h4>Account Fines</h4>
          <p className="fines-status" style={{ color: statusColor }}>
            {hasPending ? 'Outstanding' : 'All Paid'}
          </p>
        </div>
        <div className="fines-amount" style={{ color: statusColor }}>
          ${fines.total_pending.toFixed(2)}
        </div>
      </div>

      {hasPending && (
        <p className="fines-warning">
          ⚠️ You have outstanding fines. Please settle them to avoid service restrictions.
        </p>
      )}

      {fines.total_paid > 0 && (
        <p className="fines-paid">
          Paid: ${fines.total_paid.toFixed(2)}
        </p>
      )}

      {fines.fines && fines.fines.length > 0 && (
        <>
          <button
            className="view-details-btn"
            onClick={() => setShowDetails(!showDetails)}
          >
            {showDetails ? 'Hide Details' : 'View Details'} ({fines.fines.length})
          </button>

          {showDetails && (
            <div className="fines-details">
              {fines.fines.map((fine) => (
                <div
                  key={fine.fine_id}
                  className={`fine-item fine-${fine.status}`}
                >
                  <div className="fine-left">
                    <div className="fine-book">{fine.book_title || 'Unknown Book'}</div>
                    <div className="fine-reason">{fine.reason || 'Overdue fine'}</div>
                  </div>
                  <div className="fine-right">
                    <div className="fine-amount">${fine.amount.toFixed(2)}</div>
                    <div className={`fine-badge fine-badge-${fine.status}`}>
                      {fine.status.charAt(0).toUpperCase() + fine.status.slice(1)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {(!fines.fines || fines.fines.length === 0) && !hasPending && (
        <p style={{ color: '#94a3b8', marginTop: '1rem' }}>✅ No fines on your account.</p>
      )}
    </div>
  );
};

export default FinesCard;
