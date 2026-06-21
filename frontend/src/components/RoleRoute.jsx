import { Navigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { ROLE_HOME } from '../config/navigation'

export default function RoleRoute({ allowedRoles, children }) {
  const { role, isAuthenticated } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (!allowedRoles.includes(role)) {
    return <Navigate to="/403" replace />
  }

  return children
}
