/**
 * Toast Notification Component
 *
 * Displays temporary notification messages for success, error, warning, or info.
 * Auto-dismisses after 5 seconds.
 */
import { useEffect } from 'react'
import '../styles/toast.css'

const Toast = ({ message, type = 'info', onClose }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose()
    }, 5000)

    return () => clearTimeout(timer)
  }, [onClose])

  const getIcon = () => {
    switch (type) {
      case 'success':
        return '✓'
      case 'error':
        return '✕'
      case 'warning':
        return '⚠'
      default:
        return 'ℹ'
    }
  }

  return (
    <div className={`toast toast-${type}`}>
      <div className="toast-icon">{getIcon()}</div>
      <div className="toast-message">{message}</div>
      <button className="toast-close" onClick={onClose}>
        ×
      </button>
    </div>
  )
}

export default Toast
