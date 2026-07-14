import { api } from './axios'

export async function getEmployees() {
  const { data } = await api.get('/employees')
  return data
}

export async function createEmployee(payload) {
  const { data } = await api.post('/employees', payload)
  return data
}

export async function updateEmployee(id, payload) {
  const { data } = await api.put(`/employees/${id}`, payload)
  return data
}

export async function deleteEmployee(id) {
  await api.delete(`/employees/${id}`)
}
