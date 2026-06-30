import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Request interceptor — attach JWT ─────────────────────────────────────────
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('finsense_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Response interceptor — handle 401 ────────────────────────────────────────
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('finsense_token')
      localStorage.removeItem('finsense_user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export default client
