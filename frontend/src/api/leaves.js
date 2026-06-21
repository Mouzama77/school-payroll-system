import { api } from './axios'

export async function createLeaveRequest(payload) {
  const { data } = await api.post('/leaves/', payload)
  return data
}

export async function getMyLeaves() {
  const { data } = await api.get('/leaves/my')
  return data
}

export async function getLeaves() {
  const { data } = await api.get('/leaves/')
  return data
}

export async function updateLeaveStatus(id, status) {
  const { data } = await api.put(`/leaves/${id}`, { status })
  return data
}
