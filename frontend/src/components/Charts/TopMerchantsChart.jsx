import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import { formatCurrency, CHART_COLORS } from '../../utils/format'
import EmptyState from '../UI/EmptyState'

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="bg-surface-800 border border-surface-600 rounded-xl px-4 py-3 shadow-xl">
      <p className="text-white font-semibold text-sm">{d.merchant}</p>
      <p className="text-slate-300">{formatCurrency(d.total)}</p>
      <p className="text-slate-500 text-xs">{d.count} transactions</p>
    </div>
  )
}

export default function TopMerchantsChart({ data = [] }) {
  if (!data.length) return <EmptyState icon="🏪" message="No merchant data" />

  const chartData = data.slice(0, 8).map(d => ({
    ...d,
    total: Number(d.total)
  }))
  // Fixed height: 8 bars × 38px each + margins — no dynamic height on ResponsiveContainer
  const height = Math.max(200, chartData.length * 38)

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 4, right: 16, left: 8, bottom: 4 }}
          barSize={18}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
          <XAxis
            type="number"
            tickFormatter={(v) => `₹${v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v}`}
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="merchant"
            tick={{ fill: '#cbd5e1', fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            width={90}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(99,102,241,0.08)' }} />
          <Bar dataKey="total" radius={[0, 6, 6, 0]}>
            {chartData.map((_, i) => (
              <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} fillOpacity={0.85} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
