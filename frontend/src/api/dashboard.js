import { api } from './axios'

export async function getAdminDashboard() {
  const { data } = await api.get('/dashboard/admin')
  return data
}

export async function getHRDashboard() {
  const { data } = await api.get('/dashboard/hr')
  return data
}

export async function getEmployeeDashboard() {
  const { data } = await api.get('/dashboard/employee')
  return data
}

export async function getReports(month, year) {
  const { data } = await api.get('/dashboard/reports', {
    params: { month, year },
  })
  return data
}
