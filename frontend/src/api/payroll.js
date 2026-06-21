import { api } from './axios'

export async function generatePayroll(payload) {
  const { data } = await api.post('/payroll/generate', payload)
  return data
}

export async function getPayroll(employeeId, month, year) {
  const { data } = await api.get(`/payroll/${employeeId}`, {
    params: { month, year },
  })
  return data
}
