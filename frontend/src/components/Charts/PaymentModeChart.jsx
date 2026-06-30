import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { formatCurrency, modeLabel, CHART_COLORS } from '../../utils/format'
import EmptyState from '../UI/EmptyState'

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="bg-surface-800 border border-surface-600 rounded-xl px-4 py-3 shadow-xl">
      <p className="text-white font-semibold text-sm">{modeLabel(d.payment_mode)}</p>
      <p className="text-slate-300">{formatCurrency(d.total)}</p>
      <p className="text-slate-500 text-xs">{d.percentage}% · {d.count} txns</p>
    </div>
  )
}

export default function PaymentModeChart({ data = [] }) {
  if (!data.length) return <EmptyState icon="💳" message="No payment mode data" />

  const chartData = data.map(d => ({
    ...d,
    name: modeLabel(d.payment_mode),
    total: Number(d.total)
  }))

  return (
    <div style={{ width: '100%', height: 260 }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            dataKey="total"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={95}
            paddingAngle={4}
            strokeWidth={0}
          >
            {chartData.map((_, i) => (
              <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            formatter={(value, entry) => (
              <span className="text-xs text-slate-400">
                {value} <span className="text-slate-300 font-medium">{entry.payload.percentage}%</span>
              </span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
