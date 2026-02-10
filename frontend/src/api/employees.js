/**
 * Employee API client for admin operations.
 *
 * All endpoints require authentication.
 */
import client from './client'

/**
 * Get list of all employees with optional filter.
 *
 * @param {boolean|null} isActive - Filter by active status (true/false/null for all)
 * @returns {Promise<Array>} List of employees
 */
export const getEmployees = async (isActive = null) => {
  const params = {}
  if (isActive !== null) {
    params.is_active = isActive
  }

  const response = await client.get('/employees', { params })
  return response.data
}

/**
 * Get single employee by ID.
 *
 * @param {number} id - Employee ID
 * @returns {Promise<Object>} Employee data
 */
export const getEmployee = async (id) => {
  const response = await client.get(`/employees/${id}`)
  return response.data
}

/**
 * Create new employee.
 *
 * @param {Object} data - Employee data (name, job_role, daily_rate, clock_code)
 * @returns {Promise<Object>} Created employee
 */
export const createEmployee = async (data) => {
  const response = await client.post('/employees', data)
  return response.data
}

/**
 * Update employee.
 *
 * @param {number} id - Employee ID
 * @param {Object} data - Fields to update
 * @returns {Promise<Object>} Updated employee
 */
export const updateEmployee = async (id, data) => {
  const response = await client.patch(`/employees/${id}`, data)
  return response.data
}

/**
 * Deactivate employee (soft delete).
 *
 * @param {number} id - Employee ID
 * @returns {Promise<Object>} Deactivated employee
 */
export const deactivateEmployee = async (id) => {
  const response = await client.delete(`/employees/${id}`)
  return response.data
}
