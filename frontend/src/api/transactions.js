import client from './client'

export const listTransactions = (params = {}) =>
  client.get('/transactions/', { params }).then(r => r.data)

export const createTransaction = (data) =>
  client.post('/transactions/', data).then(r => r.data)

export const updateTransaction = (id, data) =>
  client.put(`/transactions/${id}`, data).then(r => r.data)

// DELETE returns 204 No Content — do not chain .then(r => r.data)
export const deleteTransaction = (id) =>
  client.delete(`/transactions/${id}`)

// Voice logging — POST /transactions/voice
export const logVoiceTransaction = (text) =>
  client.post('/transactions/voice', { text }).then(r => r.data)

export const parseVoiceTransaction = (text) =>
  client.post('/transactions/voice/parse', { text }).then(r => r.data)
