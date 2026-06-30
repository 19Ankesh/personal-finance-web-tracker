// ── Currency ──────────────────────────────────────────────────────────────────

/** Format a number as Indian Rupees: ₹1,23,456 */
export const formatCurrency = (amount) => {
  if (amount == null) return '₹0'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(Number(amount))
}

/** Format a number as Indian Rupees with decimals: ₹1,234.56 */
export const formatCurrencyFull = (amount) => {
  if (amount == null) return '₹0.00'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
  }).format(Number(amount))
}

// ── Dates ─────────────────────────────────────────────────────────────────────

/** Format a date string to "25 Jun 2025" */
export const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
}

/** Return ISO date string (YYYY-MM-DD) for N days ago */
export const daysAgo = (n) => {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toISOString().split('T')[0]
}

/** Return ISO date string for today */
export const today = () => new Date().toISOString().split('T')[0]

/** Return ISO date string for 6 months ago */
export const sixMonthsAgo = () => {
  const d = new Date()
  d.setMonth(d.getMonth() - 6)
  return d.toISOString().split('T')[0]
}

// ── Payment mode ──────────────────────────────────────────────────────────────

const MODE_LABELS = {
  upi:         'UPI',
  debit_card:  'Debit Card',
  credit_card: 'Credit Card',
  net_banking: 'Net Banking',
  cash:        'Cash',
  other:       'Other',
}

export const modeLabel = (mode) => MODE_LABELS[mode] || mode

// ── Chart colors ──────────────────────────────────────────────────────────────

export const CHART_COLORS = [
  '#818cf8', // indigo-400
  '#a78bfa', // violet-400
  '#f472b6', // pink-400
  '#34d399', // emerald-400
  '#fbbf24', // amber-400
  '#60a5fa', // blue-400
  '#f87171', // red-400
  '#22d3ee', // cyan-400
  '#fb923c', // orange-400
  '#a3e635', // lime-400
]

// ── Text ──────────────────────────────────────────────────────────────────────

/** Truncate string to max length */
export const truncate = (str, max = 30) =>
  str?.length > max ? str.slice(0, max) + '…' : (str || '')

/** Capitalize first letter */
export const capitalize = (str) =>
  str ? str.charAt(0).toUpperCase() + str.slice(1) : ''
