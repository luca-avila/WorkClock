/**
 * Kiosk Page - Full-screen clock-in/out interface for employees.
 *
 * Features:
 * - Real-time clock display
 * - 3x4 numeric keypad for PIN entry
 * - Large status messages (success/error)
 * - Auto-clear after 5 seconds
 * - Touch-friendly design
 */
import { useState, useEffect } from 'react'
import { clockAction } from '../api/kiosk'
import '../styles/kiosk.css'

const KioskPage = () => {
  const [pin, setPin] = useState('')
  const [currentTime, setCurrentTime] = useState(new Date())
  const [status, setStatus] = useState(null) // { type: 'success'|'error', message: string }
  const [loading, setLoading] = useState(false)

  // Update clock every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)

    return () => clearInterval(timer)
  }, [])

  // Auto-clear status after 5 seconds
  useEffect(() => {
    if (status) {
      const timer = setTimeout(() => {
        setStatus(null)
        setPin('')
      }, 5000)

      return () => clearTimeout(timer)
    }
  }, [status])

  const handleNumberClick = (number) => {
    if (pin.length < 4 && !loading) {
      setPin(pin + number)
    }
  }

  const handleClear = () => {
    setPin('')
    setStatus(null)
  }

  const handleEnter = async () => {
    if (pin.length !== 4 || loading) return

    setLoading(true)
    setStatus(null)

    try {
      const result = await clockAction(pin)

      // Success message
      const actionText = result.action === 'IN' ? 'Clocked IN' : 'Clocked OUT'
      const timestamp = new Date(result.timestamp).toLocaleTimeString()

      setStatus({
        type: 'success',
        message: `Welcome ${result.employee_name}!`,
        details: `${actionText} at ${timestamp}`
      })
    } catch (error) {
      // Error message
      const message = error.response?.data?.detail || 'Invalid code - please try again'

      setStatus({
        type: 'error',
        message: message
      })
    } finally {
      setLoading(false)
    }
  }

  const formatTime = () => {
    return currentTime.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    })
  }

  const formatDate = () => {
    return currentTime.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  return (
    <div className="kiosk-container">
      {/* Header with clock */}
      <div className="kiosk-header">
        <div className="kiosk-time">{formatTime()}</div>
        <div className="kiosk-date">{formatDate()}</div>
      </div>

      {/* Main content area */}
      <div className="kiosk-main">
        <h1 className="kiosk-title">WorkClock</h1>

        {/* Status message */}
        {status && (
          <div className={`kiosk-status kiosk-status-${status.type}`}>
            <div className="kiosk-status-message">{status.message}</div>
            {status.details && (
              <div className="kiosk-status-details">{status.details}</div>
            )}
          </div>
        )}

        {/* PIN display */}
        {!status && (
          <>
            <div className="kiosk-instruction">
              Enter your 4-digit PIN
            </div>
            <div className="kiosk-pin-display">
              {pin.split('').map((_, index) => (
                <div key={index} className="kiosk-pin-dot">●</div>
              ))}
              {[...Array(4 - pin.length)].map((_, index) => (
                <div key={`empty-${index}`} className="kiosk-pin-dot empty">○</div>
              ))}
            </div>

            {/* Numeric keypad */}
            <div className="kiosk-keypad">
              <div className="kiosk-keypad-row">
                {[1, 2, 3].map(num => (
                  <button
                    key={num}
                    className="kiosk-key kiosk-key-number"
                    onClick={() => handleNumberClick(num.toString())}
                    disabled={loading}
                  >
                    {num}
                  </button>
                ))}
              </div>
              <div className="kiosk-keypad-row">
                {[4, 5, 6].map(num => (
                  <button
                    key={num}
                    className="kiosk-key kiosk-key-number"
                    onClick={() => handleNumberClick(num.toString())}
                    disabled={loading}
                  >
                    {num}
                  </button>
                ))}
              </div>
              <div className="kiosk-keypad-row">
                {[7, 8, 9].map(num => (
                  <button
                    key={num}
                    className="kiosk-key kiosk-key-number"
                    onClick={() => handleNumberClick(num.toString())}
                    disabled={loading}
                  >
                    {num}
                  </button>
                ))}
              </div>
              <div className="kiosk-keypad-row">
                <button
                  className="kiosk-key kiosk-key-clear"
                  onClick={handleClear}
                  disabled={loading}
                >
                  Clear
                </button>
                <button
                  className="kiosk-key kiosk-key-number"
                  onClick={() => handleNumberClick('0')}
                  disabled={loading}
                >
                  0
                </button>
                <button
                  className="kiosk-key kiosk-key-enter"
                  onClick={handleEnter}
                  disabled={pin.length !== 4 || loading}
                >
                  {loading ? '...' : 'Enter'}
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Footer */}
      <div className="kiosk-footer">
        <div className="kiosk-footer-text">
          Need help? Contact your supervisor
        </div>
      </div>
    </div>
  )
}

export default KioskPage
