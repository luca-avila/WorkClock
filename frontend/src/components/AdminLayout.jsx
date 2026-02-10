/**
 * Admin Layout - Wrapper for admin pages with navigation and logout.
 *
 * Provides consistent header with navigation links and logout button.
 */
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import '../styles/admin.css'

const AdminLayout = ({ children }) => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const isActive = (path) => location.pathname === path

  return (
    <div className="admin-layout">
      {/* Navigation Header */}
      <nav className="admin-nav">
        <div className="admin-nav-content">
          <div className="admin-nav-brand">
            <Link to="/admin" className="brand-link">
              <span className="brand-icon">⏱️</span>
              <span className="brand-text">WorkClock Admin</span>
            </Link>
          </div>

          <div className="admin-nav-links">
            <Link
              to="/admin"
              className={`nav-link ${isActive('/admin') ? 'active' : ''}`}
            >
              Dashboard
            </Link>
            <Link
              to="/admin/employees"
              className={`nav-link ${isActive('/admin/employees') ? 'active' : ''}`}
            >
              Employees
            </Link>
            <Link
              to="/admin/shifts"
              className={`nav-link ${isActive('/admin/shifts') ? 'active' : ''}`}
            >
              Shifts
            </Link>
          </div>

          <div className="admin-nav-user">
            <span className="user-email">{user?.email}</span>
            <button className="btn btn-logout" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="admin-main">
        {children}
      </main>

      {/* Footer */}
      <footer className="admin-footer">
        <div className="admin-footer-content">
          <span>WorkClock v1.0 • {new Date().getFullYear()}</span>
          <Link to="/kiosk" className="footer-link">
            Go to Kiosk →
          </Link>
        </div>
      </footer>
    </div>
  )
}

export default AdminLayout
