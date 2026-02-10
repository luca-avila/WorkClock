/**
 * Shifts Page - View and analyze employee shifts.
 *
 * Features:
 * - List all shifts with filters (employee, date range)
 * - Pagination for large datasets
 * - Monthly payment reports
 * - Duration calculation
 */
import { useState, useEffect } from 'react'
import { getShifts, getMonthlyReport } from '../api/shifts'
import { getEmployees } from '../api/employees'
import '../styles/admin.css'

const ShiftsPage = () => {
  const [shifts, setShifts] = useState([])
  const [employees, setEmployees] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Filters
  const [filters, setFilters] = useState({
    employee_id: '',
    start_date: '',
    end_date: '',
    limit: 50,
    offset: 0
  })

  // Monthly report
  const [showReport, setShowReport] = useState(false)
  const [reportData, setReportData] = useState(null)
  const [reportLoading, setReportLoading] = useState(false)
  const [reportYear, setReportYear] = useState(new Date().getFullYear())
  const [reportMonth, setReportMonth] = useState(new Date().getMonth() + 1)

  // Load employees for filter dropdown
  useEffect(() => {
    loadEmployees()
  }, [])

  // Load shifts when filters change
  useEffect(() => {
    loadShifts()
  }, [filters])

  const loadEmployees = async () => {
    try {
      const data = await getEmployees(true) // Only active employees
      setEmployees(data)
    } catch (err) {
      console.error('Failed to load employees:', err)
    }
  }

  const loadShifts = async () => {
    try {
      setLoading(true)
      setError(null)

      const params = {}
      if (filters.employee_id) params.employee_id = parseInt(filters.employee_id)
      if (filters.start_date) params.start_date = filters.start_date
      if (filters.end_date) params.end_date = filters.end_date
      params.limit = filters.limit
      params.offset = filters.offset

      const data = await getShifts(params)
      setShifts(data.shifts)
      setTotal(data.total)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load shifts')
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (e) => {
    const { name, value } = e.target
    setFilters(prev => ({ ...prev, [name]: value, offset: 0 }))
  }

  const handleClearFilters = () => {
    setFilters({
      employee_id: '',
      start_date: '',
      end_date: '',
      limit: 50,
      offset: 0
    })
  }

  const handlePageChange = (direction) => {
    setFilters(prev => ({
      ...prev,
      offset: direction === 'next'
        ? prev.offset + prev.limit
        : Math.max(0, prev.offset - prev.limit)
    }))
  }

  const calculateDuration = (startedAt, endedAt) => {
    const start = new Date(startedAt)
    const end = new Date(endedAt)
    const diff = end - start
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
    return `${hours}h ${minutes}m`
  }

  const handleGenerateReport = async () => {
    try {
      setReportLoading(true)
      const data = await getMonthlyReport(reportYear, reportMonth)
      setReportData(data)
      setShowReport(true)
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to generate report')
    } finally {
      setReportLoading(false)
    }
  }

  const currentPage = Math.floor(filters.offset / filters.limit) + 1
  const totalPages = Math.ceil(total / filters.limit)

  return (
    <div className="admin-container">
      <div className="admin-header">
        <h1>Shift Reports</h1>
        <button className="btn btn-primary" onClick={() => setShowReport(true)}>
          📊 Monthly Report
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="filters-section">
        <div className="filters-grid">
          <div className="form-group">
            <label htmlFor="employee_id">Employee</label>
            <select
              id="employee_id"
              name="employee_id"
              value={filters.employee_id}
              onChange={handleFilterChange}
            >
              <option value="">All Employees</option>
              {employees.map(emp => (
                <option key={emp.id} value={emp.id}>
                  {emp.name} ({emp.clock_code})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="start_date">Start Date</label>
            <input
              type="date"
              id="start_date"
              name="start_date"
              value={filters.start_date}
              onChange={handleFilterChange}
            />
          </div>

          <div className="form-group">
            <label htmlFor="end_date">End Date</label>
            <input
              type="date"
              id="end_date"
              name="end_date"
              value={filters.end_date}
              onChange={handleFilterChange}
            />
          </div>

          <div className="form-group">
            <label>&nbsp;</label>
            <button className="btn btn-secondary" onClick={handleClearFilters}>
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Shifts table */}
      {loading ? (
        <div className="loading">Loading shifts...</div>
      ) : shifts.length === 0 ? (
        <div className="empty-state">
          No shifts found. Employees will appear here after they clock in and out.
        </div>
      ) : (
        <>
          <div className="table-info">
            Showing {filters.offset + 1}-{Math.min(filters.offset + filters.limit, total)} of {total} shifts
          </div>

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
                {shifts.map(shift => (
                  <tr key={shift.id}>
                    <td>{shift.employee_name}</td>
                    <td>{new Date(shift.started_at).toLocaleString()}</td>
                    <td>{new Date(shift.ended_at).toLocaleString()}</td>
                    <td>{calculateDuration(shift.started_at, shift.ended_at)}</td>
                    <td className="monospace">${shift.money_gained}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="btn btn-secondary"
                onClick={() => handlePageChange('prev')}
                disabled={filters.offset === 0}
              >
                ← Previous
              </button>
              <span className="pagination-info">
                Page {currentPage} of {totalPages}
              </span>
              <button
                className="btn btn-secondary"
                onClick={() => handlePageChange('next')}
                disabled={filters.offset + filters.limit >= total}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}

      {/* Monthly Report Modal */}
      {showReport && (
        <div className="modal-overlay" onClick={() => setShowReport(false)}>
          <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Monthly Payment Report</h2>
              <button className="modal-close" onClick={() => setShowReport(false)}>
                ×
              </button>
            </div>

            <div className="modal-body">
              {/* Report inputs */}
              <div className="report-inputs">
                <div className="form-group">
                  <label htmlFor="reportYear">Year</label>
                  <input
                    type="number"
                    id="reportYear"
                    value={reportYear}
                    onChange={(e) => setReportYear(parseInt(e.target.value))}
                    min="2000"
                    max="2100"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="reportMonth">Month</label>
                  <select
                    id="reportMonth"
                    value={reportMonth}
                    onChange={(e) => setReportMonth(parseInt(e.target.value))}
                  >
                    <option value="1">January</option>
                    <option value="2">February</option>
                    <option value="3">March</option>
                    <option value="4">April</option>
                    <option value="5">May</option>
                    <option value="6">June</option>
                    <option value="7">July</option>
                    <option value="8">August</option>
                    <option value="9">September</option>
                    <option value="10">October</option>
                    <option value="11">November</option>
                    <option value="12">December</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>&nbsp;</label>
                  <button
                    className="btn btn-primary"
                    onClick={handleGenerateReport}
                    disabled={reportLoading}
                  >
                    {reportLoading ? 'Generating...' : 'Generate Report'}
                  </button>
                </div>
              </div>

              {/* Report results */}
              {reportData && (
                <div className="report-results">
                  <h3>Report for {reportData.month}</h3>

                  {reportData.employees.length === 0 ? (
                    <div className="empty-state">No shifts found for this month.</div>
                  ) : (
                    <>
                      <table className="admin-table">
                        <thead>
                          <tr>
                            <th>Employee</th>
                            <th>Total Shifts</th>
                            <th>Total Payment</th>
                          </tr>
                        </thead>
                        <tbody>
                          {reportData.employees.map(emp => (
                            <tr key={emp.employee_id}>
                              <td>{emp.employee_name}</td>
                              <td>{emp.total_shifts}</td>
                              <td className="monospace">${emp.total_payment}</td>
                            </tr>
                          ))}
                        </tbody>
                        <tfoot>
                          <tr className="report-total">
                            <td><strong>Grand Total</strong></td>
                            <td><strong>{reportData.employees.reduce((sum, emp) => sum + emp.total_shifts, 0)}</strong></td>
                            <td className="monospace"><strong>${reportData.grand_total}</strong></td>
                          </tr>
                        </tfoot>
                      </table>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ShiftsPage
