import client from './client'

/**
 * Login with email and password
 * @param {string} email - Admin email
 * @param {string} password - Admin password
 * @returns {Promise<{access_token: string, token_type: string}>}
 */
export const login = async (email, password) => {
  const response = await client.post('/auth/login', {
    email,
    password,
  })
  return response.data
}

/**
 * Logout (client-side only - remove token)
 */
export const logout = () => {
  localStorage.removeItem('token')
}
