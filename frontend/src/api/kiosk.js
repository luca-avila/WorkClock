/**
 * Kiosk API client for clock-in/out operations.
 *
 * Public endpoint - no authentication required.
 */
import client from './client'

/**
 * Process clock action (IN or OUT) for an employee.
 *
 * @param {string} clockCode - 4-digit employee clock code
 * @returns {Promise<{action: string, employee_name: string, timestamp: string}>}
 * @throws {Error} If clock code is invalid or employee is inactive
 */
export const clockAction = async (clockCode) => {
  const response = await client.post('/kiosk/clock', {
    clock_code: clockCode
  })
  return response.data
}
