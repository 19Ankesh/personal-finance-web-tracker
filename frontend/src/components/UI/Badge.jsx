import { modeLabel } from '../../utils/format'

const CATEGORY_COLORS = {
  'Food':        'badge-amber',
  'Transport':   'badge-blue',
  'Shopping':    'badge-violet',
  'Bills':       'badge-red',
  'Health':      'badge-green',
  'Groceries':   'badge-green',
  'Entertainment': 'badge-indigo',
  'Uncategorized': 'badge-slate',
}

const MODE_COLORS = {
  upi:         'badge-indigo',
  debit_card:  'badge-blue',
  credit_card: 'badge-violet',
  net_banking: 'badge-amber',
  cash:        'badge-green',
  other:       'badge-slate',
}

export function CategoryBadge({ name }) {
  const cls = CATEGORY_COLORS[name] || 'badge-slate'
  return <span className={cls}>{name || 'Uncategorized'}</span>
}

export function PaymentModeBadge({ mode }) {
  const cls = MODE_COLORS[mode] || 'badge-slate'
  return <span className={cls}>{modeLabel(mode)}</span>
}

export function SourceBadge({ source }) {
  const map = {
    manual: 'badge-slate',
    csv:    'badge-blue',
    pdf:    'badge-amber',
    voice:  'badge-violet',
  }
  return <span className={map[source] || 'badge-slate'}>{source?.toUpperCase()}</span>
}
