/**
 * Shifts API client for reporting and analytics.
 *
 * All endpoints require authentication.
 */
import client from './client'

/**
 * Get list of shifts with optional filters.
 *
 * @param {Object} params - Query parameters
 * @param {number} params.employee_id - Filter by employee ID (optional)
 * @param {string} params.start_date - Start date YYYY-MM-DD (optional)
 * @param {string} params.end_date - End date YYYY-MM-DD (optional)
 * @param {number} params.limit - Max results (default 50)
 * @param {number} params.offset - Pagination offset (default 0)
 * @returns {Promise<{shifts: Array, total: number}>}
 */
export const getShifts = async (params = {}) => {
  const response = await client.get('/shifts', { params })
  return response.data
}

/**
 * Get monthly payment report.
 *
 * @param {number} year - Year (e.g., 2026)
 * @param {number} month - Month (1-12)
 * @returns {Promise<{month: string, employees: Array, grand_total: string}>}
 */
export const getMonthlyReport = async (year, month) => {
  const response = await client.get('/shifts/monthly-report', {
    params: { year, month }
  })
  return response.data
}
