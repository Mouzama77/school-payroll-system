import { Navigate, Route, Routes } from 'react-router-dom'

import ProtectedRoute from './components/ProtectedRoute'
import RoleRoute from './components/RoleRoute'
import { ROLE_HOME } from './config/navigation'
import { ROUTE_PERMISSIONS } from './config/permissions'
import { useAuth } from './context/AuthContext'
import Attendance from './pages/Attendance'
import ChangePassword from './pages/ChangePassword'
import Dashboard from './pages/Dashboard'
import Departments from './pages/Departments'
import Employees from './pages/Employees'
import Forbidden from './pages/Forbidden'
import ForgotPassword from './pages/ForgotPassword'
import LeaveApproval from './pages/LeaveApproval'
import Login from './pages/Login'
import MyAttendance from './pages/MyAttendance'
import MyLeaves from './pages/MyLeaves'
import MyPayroll from './pages/MyPayroll'
import MyProfile from './pages/MyProfile'
import Payroll from './pages/Payroll'
import Register from './pages/Register'
import Reports from './pages/Reports'
import ResetPassword from './pages/ResetPassword'
import Settings from './pages/Settings'
import Users from './pages/Users'

function MustChangePasswordGuard({ children }) {
  const { mustChangePassword, isAuthenticated } = useAuth()
  if (isAuthenticated && mustChangePassword) {
    return <Navigate to="/change-password" replace />
  }
  return children
}

function HomeRedirect() {
  const { role, isAuthenticated } = useAuth()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <Navigate to={ROLE_HOME[role] || '/dashboard'} replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route
        path="/403"
        element={
          <ProtectedRoute>
            <Forbidden />
          </ProtectedRoute>
        }
      />
      <Route
        path="/change-password"
        element={
          <ProtectedRoute>
            <ChangePassword />
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard"
        element={
          <RoleRoute allowedRoles={ROUTE_PERMISSIONS.dashboard}>
            <MustChangePasswordGuard>
              <Dashboard />
            </MustChangePasswordGuard>
          </RoleRoute>
        }
      />

      <Route
        path="/users"
        element={
          <RoleRoute allowedRoles={ROUTE_PERMISSIONS.users}>
            <MustChangePasswordGuard>
              <Users />
            </MustChangePasswordGuard>
          </RoleRoute>
        }
      />
      <Route
        path="/departments"
        element={
          <RoleRoute allowedRoles={ROUTE_PERMISSIONS.departments}>
            <MustChangePasswordGuard>
              <Departments />
            </MustChangePasswordGuard>
          </RoleRoute>
        }
      />
      <Route
        path="/employees"
        element={
          <RoleRoute allowedRoles={ROUTE_PERMISSIONS.employees}>
            <MustChangePasswordGuard>
              <Employees />
            </MustChangePasswordGuard>
          </RoleRoute>
        }
      />
      <Route
        path="/attendance"
        element={
          <RoleRoute allowedRoles={ROUTE_PERMISSIONS.attendance}>
            <MustChangePasswordGuard>
              <Attendance />
            </MustChangePasswordGuard>
          </RoleRoute>
        }
      />
      <Route
        path="/payroll"
        element={
          <RoleRoute allowedRoles={ROUTE_PERMISSIONS.payroll}>
            <MustChangePasswordGuard>
              <Payroll />
            </MustChangePasswordGuard>
          </RoleRoute>
        }
      />
      <Route
        path="/reports"
        element={
          <RoleRoute allowedRoles={ROUTE_PERMISSIONS.reports}>
            <MustChangePasswordGuard>
              <Reports />
            </MustChangePasswordGuard>
          </RoleRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <RoleRoute allowedRoles={ROUTE_PERMISSIONS.settings}>
            <MustChangePasswordGuard>
              <Settings />
            </MustChangePasswordGuard>
          </RoleRoute>
        }
      />
      <Route
        path="/leaves"
        element={
          <RoleRoute allowedRoles={ROUTE_PERMISSIONS.leaves}>
            <MustChangePasswordGuard>
              <LeaveApproval />
            </MustChangePasswordGuard>
          </RoleRoute>
        }
      />

      <Route
        path="/my-attendance"
        element={
          <RoleRoute allowedRoles={ROUTE_PERMISSIONS.myAttendance}>
            <MustChangePasswordGuard>
              <MyAttendance />
            </MustChangePasswordGuard>
          </RoleRoute>
        }
      />
      <Route
        path="/my-payroll"
        element={
          <RoleRoute allowedRoles={ROUTE_PERMISSIONS.myPayroll}>
            <MustChangePasswordGuard>
              <MyPayroll />
            </MustChangePasswordGuard>
          </RoleRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <RoleRoute allowedRoles={ROUTE_PERMISSIONS.profile}>
            <MustChangePasswordGuard>
              <MyProfile />
            </MustChangePasswordGuard>
          </RoleRoute>
        }
      />
      <Route
        path="/my-leaves"
        element={
          <RoleRoute allowedRoles={ROUTE_PERMISSIONS.myLeaves}>
            <MustChangePasswordGuard>
              <MyLeaves />
            </MustChangePasswordGuard>
          </RoleRoute>
        }
      />

      <Route path="/" element={<HomeRedirect />} />
      <Route path="*" element={<HomeRedirect />} />
    </Routes>
  )
}
