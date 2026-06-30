import { useState, useEffect, useCallback } from 'react'
import { useAnalytics } from '../hooks/useAnalytics'
import { getHealthScore, getInsights } from '../api/analytics'
import { formatCurrency, formatDate } from '../utils/format'
import KPICard           from '../components/UI/KPICard'
import MonthlyTrendChart from '../components/Charts/MonthlyTrendChart'
import CategoryPieChart  from '../components/Charts/CategoryPieChart'
import PaymentModeChart  from '../components/Charts/PaymentModeChart'
import TopMerchantsChart from '../components/Charts/TopMerchantsChart'
import HealthScoreCard   from '../components/UI/HealthScoreCard'
import InsightsPanel     from '../components/UI/InsightsPanel'
import { PageSpinner }   from '../components/UI/Spinner'
import ErrorState        from '../components/UI/ErrorState'

function ChartCard({ title, children }) {
  return (
    <div className="card-hover">
      <h3 className="text-sm font-semibold text-slate-300 mb-4">{title}</h3>
      {children}
    </div>
  )
}

export default function Dashboard() {
  const { data, loading, error, refetch, dateFrom, dateTo, setDateFrom, setDateTo } = useAnalytics()

  // Phase 4 state
  const [healthScore,    setHealthScore]    = useState(null)
  const [insights,       setInsights]       = useState([])
  const [healthLoading,  setHealthLoading]  = useState(true)
  const [insightLoading, setInsightLoading] = useState(true)

  const loadPhase4 = useCallback(async () => {
    setHealthLoading(true)
    setInsightLoading(true)
    try {
      const [score, tips] = await Promise.all([getHealthScore(), getInsights()])
      setHealthScore(score)
      setInsights(tips)
    } catch (e) {
      // Non-fatal — dashboard still works without Phase 4 data
      console.warn('Phase 4 data failed to load:', e)
    } finally {
      setHealthLoading(false)
      setInsightLoading(false)
    }
  }, [])

  useEffect(() => { loadPhase4() }, [loadPhase4])

  if (loading) return <PageSpinner />
  if (error)   return <ErrorState message={error} onRetry={refetch} />

  const { summary, by_category, monthly_trend, by_payment_mode, top_merchants } = data

  return (
    <div className="space-y-6 animate-fade-in max-w-7xl mx-auto">

      {/* Header + date filter */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white">Overview</h2>
          <p className="text-slate-400 text-sm mt-0.5">
            {formatDate(dateFrom)} — {formatDate(dateTo)}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Date range filter */}
          <div className="flex items-center gap-3 bg-surface-800 border border-surface-700 rounded-xl px-4 py-2">
            <label className="text-xs text-slate-400 font-medium whitespace-nowrap">From</label>
            <input
              type="date"
              className="bg-transparent text-slate-200 text-sm focus:outline-none"
              value={dateFrom}
              onChange={e => setDateFrom(e.target.value)}
            />
            <span className="text-slate-600">→</span>
            <label className="text-xs text-slate-400 font-medium whitespace-nowrap">To</label>
            <input
              type="date"
              className="bg-transparent text-slate-200 text-sm focus:outline-none"
              value={dateTo}
              onChange={e => setDateTo(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Total Spent"          value={formatCurrency(summary.total_spent)} subtitle={`${summary.tx_count} transactions`} icon="💸"  accentColor="indigo"  />
        <KPICard title="Transactions"         value={summary.tx_count.toLocaleString('en-IN')} subtitle="in this period"  icon="📋"  accentColor="violet"  />
        <KPICard title="Avg. Amount"          value={formatCurrency(summary.avg_amount)}  subtitle="per transaction"  icon="📊"  accentColor="emerald" />
        <KPICard title="Largest Transaction"  value={formatCurrency(summary.largest_tx)}  subtitle="single spend"     icon="🔝"  accentColor="amber"   />
      </div>

      {/* Health score + Insights side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <HealthScoreCard data={healthScore} loading={healthLoading} />
        </div>
        <div className="lg:col-span-2">
          <InsightsPanel insights={insights} loading={insightLoading} />
        </div>
      </div>

      {/* Monthly trend — full width */}
      <ChartCard title="📅 Monthly Spending Trend">
        <MonthlyTrendChart data={monthly_trend} />
      </ChartCard>

      {/* Category + Payment mode */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="🥧 Spending by Category">
          <CategoryPieChart data={by_category} />
        </ChartCard>
        <ChartCard title="💳 By Payment Mode">
          <PaymentModeChart data={by_payment_mode} />
        </ChartCard>
      </div>

      {/* Top merchants */}
      <ChartCard title={`🏪 Top ${top_merchants.length} Merchants`}>
        <TopMerchantsChart data={top_merchants} />
      </ChartCard>

    </div>
  )
}
