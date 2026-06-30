import client from './client'

export const getDashboard = (params = {}) =>
  client.get('/analytics/dashboard', { params }).then(r => r.data)

export const getSummary = (params = {}) =>
  client.get('/analytics/summary', { params }).then(r => r.data)

export const getByCategory = (params = {}) =>
  client.get('/analytics/by-category', { params }).then(r => r.data)

export const getMonthlyTrend = (params = {}) =>
  client.get('/analytics/monthly-trend', { params }).then(r => r.data)

export const getTopMerchants = (params = {}) =>
  client.get('/analytics/top-merchants', { params }).then(r => r.data)

export const getByPaymentMode = (params = {}) =>
  client.get('/analytics/by-payment-mode', { params }).then(r => r.data)


// Phase 4 endpoints
export const getHealthScore = () =>
  client.get('/analytics/health-score').then(r => r.data)

export const getInsights = () =>
  client.get('/analytics/insights').then(r => r.data)
