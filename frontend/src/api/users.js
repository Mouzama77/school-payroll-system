import { api } from './axios'

export async function getUsers() {
  const { data } = await api.get('/users')
  return data
}

export async function createUser(payload) {
  const { data } = await api.post('/users', payload)
  return data
}

export async function updateUser(id, payload) {
  const { data } = await api.put(`/users/${id}`, payload)
  return data
}

export async function deleteUser(id) {
  await api.delete(`/users/${id}`)
}

export async function adminResetPassword(id, payload) {
  await api.put(`/users/${id}/password`, payload)
}
