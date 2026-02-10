import { createContext, useContext, useState, useEffect } from 'react'
import { login as apiLogin, logout as apiLogout } from '../api/auth'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(null)
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Decode JWT token to get user info
  const decodeToken = (token) => {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      return { email: payload.email }
    } catch {
      return null
    }
  }

  // Load token from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('token')
    if (storedToken) {
      setToken(storedToken)
      setUser(decodeToken(storedToken))
    }
    setLoading(false)
  }, [])

  const login = async (email, password) => {
    try {
      const data = await apiLogin(email, password)
      const { access_token } = data

      // Store token
      localStorage.setItem('token', access_token)
      setToken(access_token)
      setUser(decodeToken(access_token))

      return { success: true }
    } catch (error) {
      console.error('Login error:', error)
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed. Please try again.',
      }
    }
  }

  const logout = () => {
    apiLogout()
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  const value = {
    token,
    user,
    isAuthenticated: !!token,
    loading,
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
