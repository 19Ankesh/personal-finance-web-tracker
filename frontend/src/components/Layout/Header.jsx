import { useLocation } from 'react-router-dom'

const PAGE_TITLES = {
  '/':             { title: 'Dashboard',         subtitle: 'Your financial overview' },
  '/transactions': { title: 'Transactions',      subtitle: 'Manage your spending history' },
  '/upload':       { title: 'Upload Statement',  subtitle: 'Import CSV or PDF bank statements' },
  '/mappings':     { title: 'Merchant Mappings', subtitle: 'Teach the auto-categorization engine' },
  '/budgets':      { title: 'Budgets',           subtitle: 'Track monthly spending limits by category' },
  '/goals':        { title: 'Savings Goals',     subtitle: 'Track your financial targets and progress' },
}

export default function Header() {
  const { pathname } = useLocation()
  const page = PAGE_TITLES[pathname] || { title: 'FinSense', subtitle: '' }

  return (
    <header className="flex items-center justify-between px-6 py-4 bg-surface-900 border-b border-surface-700 flex-shrink-0">
      <div>
        <h1 className="text-lg font-bold text-white">{page.title}</h1>
        {page.subtitle && <p className="text-xs text-slate-400 mt-0.5">{page.subtitle}</p>}
      </div>
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" title="Connected" />
        <span className="text-xs text-slate-500">Live</span>
      </div>
    </header>
  )
}
