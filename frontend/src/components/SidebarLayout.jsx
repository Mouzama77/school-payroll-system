import { NavLink, useNavigate } from 'react-router-dom'

import { getNavigationForRole } from '../config/permissions'
import { useAuth } from '../context/AuthContext'
import { getRoleLabel } from '../utils/auth'

const linkClass = ({ isActive }) =>
  `block rounded-lg px-3 py-2 text-sm font-medium ${
    isActive
      ? 'bg-blue-600 text-white'
      : 'text-slate-600 hover:bg-blue-50 hover:text-blue-700'
  }`

export default function SidebarLayout({ children, title }) {
  const { user, role, logout } = useAuth()
  const navigate = useNavigate()
  const navItems = getNavigationForRole(role)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen lg:flex">
      <aside className="border-b border-slate-200 bg-white lg:min-h-screen lg:w-64 lg:border-b-0 lg:border-r">
        <div className="border-b border-slate-200 px-5 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-sm font-bold text-white">
              SP
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900">School Payroll</p>
              <p className="text-xs text-slate-500">Administration Portal</p>
            </div>
          </div>
        </div>
        <nav className="space-y-1 px-4 py-4">
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to} className={linkClass}>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="flex-1">
        <header className="border-b border-slate-200 bg-white px-6 py-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-blue-600">
                {getRoleLabel(role)}
              </p>
              <h1 className="text-xl font-semibold text-slate-900">{title}</h1>
            </div>
            <div className="flex items-center gap-3">
              <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                {getRoleLabel(role)}
              </span>
              <div className="text-right">
                <p className="text-sm font-medium text-slate-900">{user?.email}</p>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="text-xs font-medium text-red-600 hover:text-red-700"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </header>
        <main className="px-6 py-8">{children}</main>
      </div>
    </div>
  )
}
