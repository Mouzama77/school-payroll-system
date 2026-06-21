import { api } from './axios'

export async function login(email, password) {
  const { data } = await api.post('/auth/login', { email, password })
  return data
}

export async function register(email, password) {
  const { data } = await api.post('/auth/register', {
    email,
    password,
    role: 'employee',
  })
  return data
}

export async function forgotPassword(email) {
  const { data } = await api.post('/auth/forgot-password', { email })
  return data
}

export async function resetPassword(token, newPassword) {
  const { data } = await api.post('/auth/reset-password', {
    token,
    new_password: newPassword,
  })
  return data
}

export async function changePassword(currentPassword, newPassword) {
  const { data } = await api.post('/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
  return data
}

export async function getMe() {
  const { data } = await api.get('/auth/me')
  return data
}
