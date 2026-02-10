/**
 * Employees Page - Admin interface for employee management.
 *
 * Features:
 * - List all employees with filter (active/inactive/all)
 * - Add new employee (modal form)
 * - Edit employee (modal form)
 * - Deactivate employee
 * - Real-time updates
 */
import { useState, useEffect } from 'react'
import { getEmployees, createEmployee, updateEmployee, deactivateEmployee } from '../api/employees'
import Toast from '../components/Toast'
import '../styles/admin.css'

const EmployeesPage = () => {
  const [employees, setEmployees] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState(null) // null = all, true = active, false = inactive
  const [showModal, setShowModal] = useState(false)
  const [editingEmployee, setEditingEmployee] = useState(null)
  const [error, setError] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    job_role: '',
    daily_rate: '',
    clock_code: ''
  })
  const [formErrors, setFormErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [deactivating, setDeactivating] = useState(null)
  const [toast, setToast] = useState(null)

  // Load employees on mount and when filter changes
  useEffect(() => {
    loadEmployees()
  }, [filter])

  const loadEmployees = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getEmployees(filter)
      setEmployees(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load employees')
    } finally {
      setLoading(false)
    }
  }

  const handleAddClick = () => {
    setEditingEmployee(null)
    setFormData({ name: '', job_role: '', daily_rate: '', clock_code: '' })
    setFormErrors({})
    setShowModal(true)
  }

  const handleEditClick = (employee) => {
    setEditingEmployee(employee)
    setFormData({
      name: employee.name,
      job_role: employee.job_role,
      daily_rate: employee.daily_rate,
      clock_code: employee.clock_code
    })
    setFormErrors({})
    setShowModal(true)
  }

  const handleDeactivate = async (employee) => {
    if (!window.confirm(`Deactivate ${employee.name}? They will not be able to clock in/out.`)) {
      return
    }

    try {
      setDeactivating(employee.id)
      await deactivateEmployee(employee.id)
      await loadEmployees()
      setToast({ message: `${employee.name} has been deactivated`, type: 'success' })
    } catch (err) {
      setToast({
        message: err.response?.data?.detail || 'Failed to deactivate employee',
        type: 'error'
      })
    } finally {
      setDeactivating(null)
    }
  }

  const validateForm = () => {
    const errors = {}

    if (!formData.name.trim()) {
      errors.name = 'Name is required'
    }

    if (!formData.job_role.trim()) {
      errors.job_role = 'Job role is required'
    }

    if (!formData.daily_rate) {
      errors.daily_rate = 'Daily rate is required'
    } else if (parseFloat(formData.daily_rate) <= 0) {
      errors.daily_rate = 'Daily rate must be greater than 0'
    }

    if (!formData.clock_code) {
      errors.clock_code = 'Clock code is required'
    } else if (!/^\d{4}$/.test(formData.clock_code)) {
      errors.clock_code = 'Clock code must be exactly 4 digits'
    }

    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    try {
      setSubmitting(true)
      if (editingEmployee) {
        await updateEmployee(editingEmployee.id, formData)
        setToast({ message: `${formData.name} has been updated`, type: 'success' })
      } else {
        await createEmployee(formData)
        setToast({ message: `${formData.name} has been created`, type: 'success' })
      }

      setShowModal(false)
      await loadEmployees()
    } catch (err) {
      const detail = err.response?.data?.detail || 'Failed to save employee'
      setToast({ message: detail, type: 'error' })
    } finally {
      setSubmitting(false)
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    // Clear error for this field when user types
    if (formErrors[name]) {
      setFormErrors(prev => ({ ...prev, [name]: '' }))
    }
  }

  return (
    <>
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
      <div className="admin-container">
      <div className="admin-header">
        <h1>Employee Management</h1>
        <button className="btn btn-primary" onClick={handleAddClick}>
          + Add Employee
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {/* Filter buttons */}
      <div className="filter-bar">
        <button
          className={`btn-filter ${filter === null ? 'active' : ''}`}
          onClick={() => setFilter(null)}
        >
          All Employees
        </button>
        <button
          className={`btn-filter ${filter === true ? 'active' : ''}`}
          onClick={() => setFilter(true)}
        >
          Active Only
        </button>
        <button
          className={`btn-filter ${filter === false ? 'active' : ''}`}
          onClick={() => setFilter(false)}
        >
          Inactive Only
        </button>
      </div>

      {/* Employee table */}
      {loading ? (
        <div className="loading">Loading employees...</div>
      ) : employees.length === 0 ? (
        <div className="empty-state">
          No employees found. Click "Add Employee" to create one.
        </div>
      ) : (
        <div className="table-container">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Job Role</th>
                <th>Daily Rate</th>
                <th>Clock Code</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {employees.map(employee => (
                <tr key={employee.id} className={!employee.is_active ? 'inactive-row' : ''}>
                  <td>{employee.name}</td>
                  <td>{employee.job_role}</td>
                  <td>${employee.daily_rate}</td>
                  <td className="monospace">{employee.clock_code}</td>
                  <td>
                    <span className={`status-badge ${employee.is_active ? 'status-active' : 'status-inactive'}`}>
                      {employee.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>{new Date(employee.created_at).toLocaleDateString()}</td>
                  <td>
                    <div className="action-buttons">
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => handleEditClick(employee)}
                      >
                        Edit
                      </button>
                      {employee.is_active && (
                        <button
                          className="btn btn-sm btn-danger"
                          onClick={() => handleDeactivate(employee)}
                          disabled={deactivating === employee.id}
                        >
                          {deactivating === employee.id ? 'Deactivating...' : 'Deactivate'}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add/Edit Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingEmployee ? 'Edit Employee' : 'Add Employee'}</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>
                ×
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="name">Name *</label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className={formErrors.name ? 'input-error' : ''}
                  placeholder="John Doe"
                />
                {formErrors.name && (
                  <span className="error-text">{formErrors.name}</span>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="job_role">Job Role *</label>
                <input
                  type="text"
                  id="job_role"
                  name="job_role"
                  value={formData.job_role}
                  onChange={handleInputChange}
                  className={formErrors.job_role ? 'input-error' : ''}
                  placeholder="Warehouse Associate"
                />
                {formErrors.job_role && (
                  <span className="error-text">{formErrors.job_role}</span>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="daily_rate">Daily Rate ($) *</label>
                <input
                  type="number"
                  id="daily_rate"
                  name="daily_rate"
                  value={formData.daily_rate}
                  onChange={handleInputChange}
                  className={formErrors.daily_rate ? 'input-error' : ''}
                  placeholder="150.00"
                  step="0.01"
                  min="0"
                />
                {formErrors.daily_rate && (
                  <span className="error-text">{formErrors.daily_rate}</span>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="clock_code">Clock Code (4 digits) *</label>
                <input
                  type="text"
                  id="clock_code"
                  name="clock_code"
                  value={formData.clock_code}
                  onChange={handleInputChange}
                  className={formErrors.clock_code ? 'input-error' : ''}
                  placeholder="1234"
                  maxLength="4"
                  pattern="\d{4}"
                />
                {formErrors.clock_code && (
                  <span className="error-text">{formErrors.clock_code}</span>
                )}
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowModal(false)}
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Saving...' : (editingEmployee ? 'Update' : 'Create')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
    </>
  )
}

export default EmployeesPage
