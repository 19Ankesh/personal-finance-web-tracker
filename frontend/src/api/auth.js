import client from './client'

export const register = (name, email, password) =>
  client.post('/auth/register', { name, email, password }).then(r => r.data)

export const login = (email, password) => {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  return client.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  }).then(r => r.data)
}

export const getMe = () =>
  client.get('/auth/me').then(r => r.data)

export const forgotPassword = (email) =>
  client.post('/auth/forgot-password', { email }).then(r => r.data)

export const resetPassword = (token, new_password) =>
  client.post('/auth/reset-password', { token, new_password }).then(r => r.data)
