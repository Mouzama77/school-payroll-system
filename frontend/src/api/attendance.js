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

export async function overrideAttendance(attendanceId, status, reason) {
  const { data } = await api.put(`/attendance/${attendanceId}/override`, { status, reason })
  return data
}
