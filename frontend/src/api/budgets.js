import client from './client'

export const listBudgets   = (params = {}) => client.get('/budgets/', { params }).then(r => r.data)
export const createBudget  = (data)        => client.post('/budgets/', data).then(r => r.data)
export const updateBudget  = (id, data)    => client.put(`/budgets/${id}`, data).then(r => r.data)
export const deleteBudget  = (id)          => client.delete(`/budgets/${id}`)
