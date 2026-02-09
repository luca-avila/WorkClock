import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import LoginPage from './pages/LoginPage'
import KioskPage from './pages/KioskPage'

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/kiosk" element={<KioskPage />} />
          <Route path="/" element={<Navigate to="/kiosk" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  )
}

export default App
