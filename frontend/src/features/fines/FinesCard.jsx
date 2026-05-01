import { useState } from 'react'
import { calculateFine, payFine } from './fineService.js'

export function FinesCard() {
  const [loanId, setLoanId] = useState('')
  const [fineAmount, setFineAmount] = useState(null)
  const [message, setMessage] = useState('')

  const handleCalculate = async () => {
    try {
      const data = await calculateFine(Number(loanId))
      setFineAmount(data.fine_amount)
      setMessage('Fine loaded successfully')
    } catch (error) {
      setMessage('Unable to calculate fine')
    }
  }

  const handlePay = async () => {
    try {
      await payFine(Number(loanId))
      setMessage('Payment successful')
    } catch (error) {
      setMessage('Unable to pay fine')
    }
  }

  return (
    <section className="fines-card">
      <h2>Fine Management</h2>
      <label>
        Loan ID
        <input value={loanId} onChange={(event) => setLoanId(event.target.value)} />
      </label>
      <div className="fines-actions">
        <button onClick={handleCalculate}>Calculate Fine</button>
        <button onClick={handlePay}>Pay Fine</button>
      </div>
      {fineAmount !== null && <p>Fine amount: {fineAmount}</p>}
      <p>{message}</p>
    </section>
  )
}
