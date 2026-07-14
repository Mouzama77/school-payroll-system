import { api } from './axios'

export async function getAcademicCalendarEntries() {
  const { data } = await api.get('/academic-calendar')
  return data
}

export async function createAcademicCalendarEntry(payload) {
  const { data } = await api.post('/academic-calendar', payload)
  return data
}
