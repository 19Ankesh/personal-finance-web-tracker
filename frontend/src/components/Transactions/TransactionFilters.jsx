import { modeLabel } from '../../utils/format'

const PAYMENT_MODES = ['', 'upi', 'debit_card', 'credit_card', 'net_banking', 'cash', 'other']

export default function TransactionFilters({ filters, onUpdate }) {
  return (
    <div className="flex flex-wrap gap-3">
      {/* Search */}
      <input
        type="text"
        className="input-sm w-48"
        placeholder="Search merchant..."
        value={filters.search}
        onChange={e => onUpdate('search', e.target.value)}
      />

      {/* Payment mode */}
      <select
        className="input-sm w-40"
        value={filters.payment_mode}
        onChange={e => onUpdate('payment_mode', e.target.value)}
      >
        <option value="">All modes</option>
        {PAYMENT_MODES.filter(Boolean).map(m => (
          <option key={m} value={m}>{modeLabel(m)}</option>
        ))}
      </select>

      {/* Date from */}
      <input
        type="date"
        className="input-sm w-38"
        value={filters.date_from}
        onChange={e => onUpdate('date_from', e.target.value)}
      />

      {/* Date to */}
      <input
        type="date"
        className="input-sm w-38"
        value={filters.date_to}
        onChange={e => onUpdate('date_to', e.target.value)}
      />
    </div>
  )
}
