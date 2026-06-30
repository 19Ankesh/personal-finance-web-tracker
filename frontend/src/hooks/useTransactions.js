import { useState, useEffect, useCallback } from 'react'
import { listTransactions } from '../api/transactions'

export function useTransactions(initialFilters = {}) {
  const [transactions, setTransactions] = useState([])
  const [loading,      setLoading]      = useState(true)
  const [error,        setError]        = useState(null)
  const [total,        setTotal]        = useState(0)
  const [filters, setFilters] = useState({
    skip: 0, limit: 20,
    search: '', category_id: '', payment_mode: '',
    date_from: '', date_to: '',
    ...initialFilters,
  })

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      // Strip empty filter values
      const params = Object.fromEntries(
        Object.entries(filters).filter(([, v]) => v !== '' && v != null)
      )
      const result = await listTransactions(params)
      // Backend returns TransactionListResponse: { items, total, skip, limit }
      const items = result.items ?? result.transactions ?? result
      setTransactions(Array.isArray(items) ? items : [])
      setTotal(result.total ?? (Array.isArray(items) ? items.length : 0))
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load transactions')
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => { fetch() }, [fetch])

  const updateFilter = (key, value) =>
    setFilters(prev => ({ ...prev, [key]: value, skip: 0 }))

  const nextPage = () =>
    setFilters(prev => ({ ...prev, skip: prev.skip + prev.limit }))

  const prevPage = () =>
    setFilters(prev => ({ ...prev, skip: Math.max(0, prev.skip - prev.limit) }))

  return {
    transactions, loading, error, total, filters,
    refetch: fetch, updateFilter, nextPage, prevPage,
  }
}
