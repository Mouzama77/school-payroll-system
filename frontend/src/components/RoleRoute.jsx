import { Navigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

export default function RoleRoute({ allowedRoles, children }) {
  const { role } = useAuth()

  if (!allowedRoles?.length || !allowedRoles.includes(role)) {
    return <Navigate to="/403" replace />
  }

  return children
}
