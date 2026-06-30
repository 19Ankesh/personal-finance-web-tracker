// HealthScoreRing — animated SVG donut ring showing the financial health score.
// Used on the Dashboard as a standalone card.

const BAND_COLORS = {
  emerald: { stroke: '#10b981', text: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
  blue:    { stroke: '#6366f1', text: 'text-indigo-400',  bg: 'bg-indigo-500/10 border-indigo-500/20' },
  amber:   { stroke: '#f59e0b', text: 'text-amber-400',   bg: 'bg-amber-500/10 border-amber-500/20' },
  red:     { stroke: '#ef4444', text: 'text-red-400',     bg: 'bg-red-500/10 border-red-500/20' },
}

function ScoreRing({ score, color }) {
  const size         = 120
  const strokeWidth  = 10
  const radius       = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset       = circumference - (Math.min(score, 100) / 100) * circumference
  const stroke       = BAND_COLORS[color]?.stroke ?? '#6366f1'

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="-rotate-90">
        {/* Track */}
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke="#1e293b" strokeWidth={strokeWidth}
        />
        {/* Score arc */}
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none"
          stroke={stroke}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}
        />
      </svg>
      {/* Score number in center */}
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-2xl font-bold text-white tabular-nums">{score}</span>
      </div>
    </div>
  )
}

function BreakdownBar({ label, value, max, color }) {
  const pct = Math.min((value / max) * 100, 100)
  const stroke = BAND_COLORS[color]?.stroke ?? '#6366f1'
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className="text-slate-300 font-medium tabular-nums">{value.toFixed(0)}/{max}</span>
      </div>
      <div className="w-full bg-surface-700 rounded-full h-1.5">
        <div
          className="h-1.5 rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: stroke }}
        />
      </div>
    </div>
  )
}

export default function HealthScoreCard({ data, loading }) {
  if (loading) {
    return (
      <div className="card animate-pulse space-y-4">
        <div className="h-4 bg-surface-700 rounded w-40" />
        <div className="flex justify-center">
          <div className="w-28 h-28 rounded-full bg-surface-700" />
        </div>
        <div className="space-y-2">
          <div className="h-3 bg-surface-700 rounded" />
          <div className="h-3 bg-surface-700 rounded" />
          <div className="h-3 bg-surface-700 rounded" />
        </div>
      </div>
    )
  }

  if (!data) return null

  const colors = BAND_COLORS[data.band_color] ?? BAND_COLORS.blue

  return (
    <div className="card space-y-5">
      {/* Title */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-white">Financial Health Score</h3>
        <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${colors.bg} ${colors.text}`}>
          {data.band}
        </span>
      </div>

      {/* Ring */}
      <div className="flex justify-center">
        <ScoreRing score={data.score} color={data.band_color} />
      </div>

      {/* Breakdown bars */}
      <div className="space-y-3 border-t border-surface-700 pt-4">
        <BreakdownBar
          label="Budget Adherence"
          value={data.budget_adherence}
          max={40}
          color={data.band_color}
        />
        <BreakdownBar
          label="Savings Progress"
          value={data.savings_progress}
          max={30}
          color={data.band_color}
        />
        <BreakdownBar
          label="Spending Consistency"
          value={data.spending_consistency}
          max={30}
          color={data.band_color}
        />
      </div>
    </div>
  )
}
