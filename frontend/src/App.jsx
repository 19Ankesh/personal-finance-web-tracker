import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Transactions from './pages/Transactions'
import Upload from './pages/Upload'
import Mappings from './pages/Mappings'
import Budgets from './pages/Budgets'
import Goals from './pages/Goals'
import ResetPassword from './pages/ResetPassword'

const TOKEN_KEY = 'finsense_token'

function ProtectedRoute() {
  const { token } = useAuth()
  const stored = localStorage.getItem(TOKEN_KEY)
  return (token || stored) ? <Outlet /> : <Navigate to="/login" replace />
}

function PublicRoute() {
  const { token } = useAuth()
  const stored = localStorage.getItem(TOKEN_KEY)
  return (token || stored) ? <Navigate to="/" replace /> : <Outlet />
}

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route element={<PublicRoute />}>
            <Route path="/login"          element={<Login />} />
            <Route path="/register"       element={<Register />} />
            <Route path="/reset-password" element={<ResetPassword />} />
          </Route>
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/"             element={<Dashboard />} />
              <Route path="/transactions" element={<Transactions />} />
              <Route path="/upload"       element={<Upload />} />
              <Route path="/mappings"     element={<Mappings />} />
              <Route path="/budgets"      element={<Budgets />} />
              <Route path="/goals"        element={<Goals />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  )
}
