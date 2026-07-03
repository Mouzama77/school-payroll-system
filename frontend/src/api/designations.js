import { api } from './axios'

export async function getDesignations() {
  const { data } = await api.get('/designations')
  return data
}

export async function createDesignation(payload) {
  const { data } = await api.post('/designations', payload)
  return data
}
