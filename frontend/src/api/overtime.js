import { api } from './axios'

export async function createOvertime(payload) {
  const { data } = await api.post('/overtime', payload)
  return data
}

export default { createOvertime }
