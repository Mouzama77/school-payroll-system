import { api } from './axios'

export async function markAttendance(payload) {
  const { data } = await api.post('/attendance/', payload)
  return data
}

export async function getMonthlyAttendance(employeeId, month, year) {
  const { data } = await api.get(`/attendance/${employeeId}`, {
    params: { month, year },
  })
  return data
}
