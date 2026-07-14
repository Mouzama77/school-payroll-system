export const ROLES = {
  ADMIN: 'admin',
  HR: 'hr',
  EMPLOYEE: 'employee',
}

export const ROLE_HOME = {
  [ROLES.ADMIN]: '/dashboard',
  [ROLES.HR]: '/dashboard',
  [ROLES.EMPLOYEE]: '/dashboard',
}

export const ROUTE_PERMISSIONS = {
  dashboard: [ROLES.ADMIN, ROLES.HR, ROLES.EMPLOYEE],
  users: [ROLES.ADMIN],
  departments: [ROLES.ADMIN],
  designations: [ROLES.ADMIN, ROLES.HR],
  employees: [ROLES.ADMIN, ROLES.HR],
  attendance: [ROLES.ADMIN, ROLES.HR],
  payroll: [ROLES.ADMIN, ROLES.HR],
  academicCalendar: [ROLES.ADMIN],
  overtime: [ROLES.ADMIN, ROLES.HR],
  leaves: [ROLES.ADMIN, ROLES.HR],
  reports: [ROLES.ADMIN],
  settings: [ROLES.ADMIN],
  auditLog: [ROLES.ADMIN],
  profile: [ROLES.EMPLOYEE],
  myAttendance: [ROLES.EMPLOYEE],
  myPayroll: [ROLES.EMPLOYEE],
  myLeaves: [ROLES.EMPLOYEE],
}

export const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', permission: 'dashboard' },
  { to: '/users', label: 'Users', permission: 'users' },
  { to: '/departments', label: 'Departments', permission: 'departments' },
  { to: '/designations', label: 'Designations', permission: 'designations' },
  { to: '/employees', label: 'Employees', permission: 'employees' },
  { to: '/attendance', label: 'Attendance', permission: 'attendance' },
  { to: '/overtime', label: 'Overtime', permission: 'overtime' },
  { to: '/academic-calendar', label: 'Academic Calendar', permission: 'academicCalendar' },
  { to: '/leaves', label: 'Leave Approval', permission: 'leaves' },
  { to: '/payroll', label: 'Payroll', permission: 'payroll' },
  { to: '/reports', label: 'Reports', permission: 'reports' },
  { to: '/audit-logs', label: 'Audit Log', permission: 'auditLog' },
  { to: '/settings', label: 'Settings', permission: 'settings' },
  { to: '/profile', label: 'My Profile', permission: 'profile' },
  { to: '/my-attendance', label: 'My Attendance', permission: 'myAttendance' },
  { to: '/my-payroll', label: 'My Payroll', permission: 'myPayroll' },
  { to: '/my-leaves', label: 'My Leaves', permission: 'myLeaves' },
]

export function canAccessPermission(role, permission) {
  return Boolean(role && ROUTE_PERMISSIONS[permission]?.includes(role))
}

export function getNavigationForRole(role) {
  return NAV_ITEMS.filter((item) => canAccessPermission(role, item.permission))
}

export const NAV_BY_ROLE = Object.values(ROLES).reduce((navigation, role) => {
  navigation[role] = getNavigationForRole(role)
  return navigation
}, {})
