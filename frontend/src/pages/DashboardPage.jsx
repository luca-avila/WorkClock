/**
 * Dashboard Page - Admin overview with statistics.
 *
 * Shows quick stats and recent activity.
 */
import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getEmployees } from '../api/employees'
import { getShifts } from '../api/shifts'
import '../styles/admin.css'

const DashboardPage = () => {
  const [stats, setStats] = useState({
    totalEmployees: 0,
    activeEmployees: 0,
    inactiveEmployees: 0,
    totalShifts: 0,
    recentShifts: []
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)

      // Load employees
      const [allEmployees, activeEmployees, inactiveEmployees] = await Promise.all([
        getEmployees(null),
        getEmployees(true),
        getEmployees(false)
      ])

      // Load recent shifts
      const shiftsData = await getShifts({ limit: 5, offset: 0 })

      setStats({
        totalEmployees: allEmployees.length,
        activeEmployees: activeEmployees.length,
        inactiveEmployees: inactiveEmployees.length,
        totalShifts: shiftsData.total,
        recentShifts: shiftsData.shifts
      })
    } catch (err) {
      console.error('Failed to load dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatDateTime = (timestamp) => {
    return new Date(timestamp).toLocaleString()
  }

  const calculateDuration = (startedAt, endedAt) => {
    const start = new Date(startedAt)
    const end = new Date(endedAt)
    const diff = end - start
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
    return `${hours}h ${minutes}m`
  }

  if (loading) {
    return (
      <div className="admin-container">
        <div className="loading">Loading dashboard...</div>
      </div>
    )
  }

  return (
    <div className="admin-container">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <p className="dashboard-subtitle">Welcome to WorkClock Admin</p>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card stat-card-primary">
          <div className="stat-icon">👥</div>
          <div className="stat-content">
            <div className="stat-value">{stats.totalEmployees}</div>
            <div className="stat-label">Total Employees</div>
          </div>
          <Link to="/admin/employees" className="stat-link">
            View all →
          </Link>
        </div>

        <div className="stat-card stat-card-success">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <div className="stat-value">{stats.activeEmployees}</div>
            <div className="stat-label">Active Employees</div>
          </div>
          <Link to="/admin/employees?filter=active" className="stat-link">
            View active →
          </Link>
        </div>

        <div className="stat-card stat-card-warning">
          <div className="stat-icon">⏸️</div>
          <div className="stat-content">
            <div className="stat-value">{stats.inactiveEmployees}</div>
            <div className="stat-label">Inactive Employees</div>
          </div>
          <Link to="/admin/employees?filter=inactive" className="stat-link">
            View inactive →
          </Link>
        </div>

        <div className="stat-card stat-card-info">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <div className="stat-value">{stats.totalShifts}</div>
            <div className="stat-label">Total Shifts</div>
          </div>
          <Link to="/admin/shifts" className="stat-link">
            View shifts →
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="dashboard-section">
        <div className="section-header">
          <h2>Recent Shifts</h2>
          <Link to="/admin/shifts" className="btn btn-secondary">
            View All
          </Link>
        </div>

        {stats.recentShifts.length === 0 ? (
          <div className="empty-state">
            No shifts yet. Employees will appear here after they clock in and out.
          </div>
        ) : (
          <div className="table-container">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>Clock In</th>
                  <th>Clock Out</th>
                  <th>Duration</th>
                  <th>Payment</th>
                </tr>
              </thead>
              <tbody>
                {stats.recentShifts.map(shift => (
                  <tr key={shift.id}>
                    <td>{shift.employee_name}</td>
                    <td>{formatDateTime(shift.started_at)}</td>
                    <td>{formatDateTime(shift.ended_at)}</td>
                    <td>{calculateDuration(shift.started_at, shift.ended_at)}</td>
                    <td className="monospace">${shift.money_gained}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="dashboard-section">
        <h2>Quick Actions</h2>
        <div className="quick-actions">
          <Link to="/admin/employees" className="action-card">
            <div className="action-icon">👤</div>
            <div className="action-title">Manage Employees</div>
            <div className="action-description">
              Add, edit, or deactivate employees
            </div>
          </Link>

          <Link to="/admin/shifts" className="action-card">
            <div className="action-icon">📈</div>
            <div className="action-title">View Reports</div>
            <div className="action-description">
              View shifts and generate monthly reports
            </div>
          </Link>

          <Link to="/kiosk" className="action-card">
            <div className="action-icon">⏱️</div>
            <div className="action-title">Open Kiosk</div>
            <div className="action-description">
              Go to employee clock-in/out kiosk
            </div>
          </Link>
        </div>
      </div>
    </div>
  )
}

export default DashboardPage
