import client from './client'

export const listCategories = () =>
  client.get('/categories/').then(r => r.data)
