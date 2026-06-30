import { useState, useEffect, useCallback } from 'react'
import { getDashboard } from '../api/analytics'
import { sixMonthsAgo, today } from '../utils/format'

export function useAnalytics(initialDateFrom, initialDateTo) {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)
  const [dateFrom, setDateFrom] = useState(initialDateFrom || sixMonthsAgo())
  const [dateTo,   setDateTo]   = useState(initialDateTo   || today())

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await getDashboard({ date_from: dateFrom, date_to: dateTo })
      setData(result)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }, [dateFrom, dateTo])

  useEffect(() => { fetch() }, [fetch])

  return { data, loading, error, refetch: fetch, dateFrom, dateTo, setDateFrom, setDateTo }
}
