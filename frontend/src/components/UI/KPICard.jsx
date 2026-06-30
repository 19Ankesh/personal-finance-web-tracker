import { formatCurrency } from '../../utils/format'

export default function KPICard({ title, value, subtitle, icon, trend, accentColor = 'indigo' }) {
  const accents = {
    indigo:  { ring: 'hover:border-indigo-500/40',  icon: 'bg-indigo-500/10 text-indigo-400', glow: 'hover:shadow-indigo-500/10' },
    violet:  { ring: 'hover:border-violet-500/40',  icon: 'bg-violet-500/10 text-violet-400', glow: 'hover:shadow-violet-500/10' },
    emerald: { ring: 'hover:border-emerald-500/40', icon: 'bg-emerald-500/10 text-emerald-400', glow: 'hover:shadow-emerald-500/10' },
    amber:   { ring: 'hover:border-amber-500/40',   icon: 'bg-amber-500/10 text-amber-400', glow: 'hover:shadow-amber-500/10' },
  }
  const a = accents[accentColor] || accents.indigo

  return (
    <div className={`card transition-all duration-300 ${a.ring} hover:shadow-lg ${a.glow} animate-slide-up`}>
      {/* Top row */}
      <div className="flex items-start justify-between mb-4">
        <span className="text-sm font-medium text-slate-400">{title}</span>
        <div className={`w-10 h-10 rounded-xl ${a.icon} flex items-center justify-center text-xl flex-shrink-0`}>
          {icon}
        </div>
      </div>

      {/* Value */}
      <div className="text-2xl font-bold text-white mb-1 tabular-nums">
        {value}
      </div>

      {/* Subtitle / trend */}
      {(subtitle || trend) && (
        <div className="flex items-center gap-2">
          {subtitle && <span className="text-slate-500 text-xs">{subtitle}</span>}
        </div>
      )}
    </div>
  )
}
