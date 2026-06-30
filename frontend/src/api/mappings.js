import client from './client'

export const listMappings = () =>
  client.get('/merchant-mappings/').then(r => r.data)

export const saveMapping = (merchant_name, category_id) =>
  client.post('/merchant-mappings/', { merchant_name, category_id }).then(r => r.data)

export const deleteMapping = (id) =>
  client.delete(`/merchant-mappings/${id}`)
