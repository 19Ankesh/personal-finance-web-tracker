import client from './client'

export const listGoals   = ()           => client.get('/savings-goals/').then(r => r.data)
export const createGoal  = (data)       => client.post('/savings-goals/', data).then(r => r.data)
export const updateGoal  = (id, data)   => client.put(`/savings-goals/${id}`, data).then(r => r.data)
export const deleteGoal  = (id)         => client.delete(`/savings-goals/${id}`)
