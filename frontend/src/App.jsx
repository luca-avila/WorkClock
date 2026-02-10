import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import AdminLayout from './components/AdminLayout'
import LoginPage from './pages/LoginPage'
import KioskPage from './pages/KioskPage'
import DashboardPage from './pages/DashboardPage'
import EmployeesPage from './pages/EmployeesPage'
import ShiftsPage from './pages/ShiftsPage'

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/kiosk" element={<KioskPage />} />
          <Route
            path="/admin"
            element={
              <ProtectedRoute>
                <AdminLayout>
                  <DashboardPage />
                </AdminLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/employees"
            element={
              <ProtectedRoute>
                <AdminLayout>
                  <EmployeesPage />
                </AdminLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/shifts"
            element={
              <ProtectedRoute>
                <AdminLayout>
                  <ShiftsPage />
                </AdminLayout>
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/kiosk" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  )
}

export default App
