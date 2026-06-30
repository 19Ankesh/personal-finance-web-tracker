import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { formatCurrency, CHART_COLORS } from '../../utils/format'
import EmptyState from '../UI/EmptyState'

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="bg-surface-800 border border-surface-600 rounded-xl px-4 py-3 shadow-xl">
      <p className="text-white font-semibold text-sm">{d.category_name}</p>
      <p className="text-slate-300">{formatCurrency(d.total)}</p>
      <p className="text-slate-500 text-xs">{d.percentage}% · {d.count} txns</p>
    </div>
  )
}

const renderLegend = ({ payload }) => (
  <ul className="flex flex-col gap-1.5 mt-2">
    {payload.map((entry, i) => (
      <li key={i} className="flex items-center gap-2 text-xs text-slate-400">
        <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: entry.color }} />
        <span className="truncate max-w-[140px]">{entry.value}</span>
        <span className="ml-auto text-slate-300 font-medium tabular-nums">
          {entry.payload.percentage}%
        </span>
      </li>
    ))}
  </ul>
)

export default function CategoryPieChart({ data = [] }) {
  if (!data.length) return <EmptyState icon="🥧" message="No category data" />

  const chartData = data.map(d => ({
    ...d,
    total: Number(d.total)
  }))

  return (
    <div style={{ width: '100%', height: 260 }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            dataKey="total"
            nameKey="category_name"
            cx="40%"
            cy="50%"
            innerRadius={55}
            outerRadius={90}
            paddingAngle={3}
            strokeWidth={0}
          >
            {chartData.map((_, i) => (
              <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            layout="vertical"
            align="right"
            verticalAlign="middle"
            content={renderLegend}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
