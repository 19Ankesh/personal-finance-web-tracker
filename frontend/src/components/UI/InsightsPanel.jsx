// InsightsPanel — renders the smart spending insights list on the Dashboard.

const SEVERITY_STYLES = {
  danger:  'border-red-500/20    bg-red-500/5    text-red-400',
  warning: 'border-amber-500/20  bg-amber-500/5  text-amber-400',
  success: 'border-emerald-500/20 bg-emerald-500/5 text-emerald-400',
  info:    'border-indigo-500/20  bg-indigo-500/5  text-indigo-400',
}

function InsightItem({ insight }) {
  const style = SEVERITY_STYLES[insight.severity] ?? SEVERITY_STYLES.info

  return (
    <div className={`flex items-start gap-3 p-3 rounded-xl border ${style} animate-slide-up`}>
      <span className="text-xl flex-shrink-0 mt-0.5">{insight.icon}</span>
      <div className="min-w-0">
        <p className="text-sm font-medium text-white leading-snug">{insight.title}</p>
        <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">{insight.message}</p>
      </div>
    </div>
  )
}

function SkeletonItem() {
  return (
    <div className="flex items-start gap-3 p-3 rounded-xl border border-surface-700 animate-pulse">
      <div className="w-7 h-7 rounded-lg bg-surface-700 flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="h-3 bg-surface-700 rounded w-3/4" />
        <div className="h-3 bg-surface-700 rounded w-full" />
      </div>
    </div>
  )
}

export default function InsightsPanel({ insights, loading }) {
  return (
    <div className="card space-y-4">
      <h3 className="font-semibold text-white">Smart Insights</h3>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => <SkeletonItem key={i} />)}
        </div>
      ) : !insights?.length ? (
        <div className="text-center py-6">
          <p className="text-3xl mb-2">💡</p>
          <p className="text-slate-400 text-sm">No insights yet</p>
          <p className="text-slate-500 text-xs mt-1">Add transactions, budgets, and goals to see insights.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {insights.map((insight, i) => (
            <InsightItem key={i} insight={insight} />
          ))}
        </div>
      )}
    </div>
  )
}
