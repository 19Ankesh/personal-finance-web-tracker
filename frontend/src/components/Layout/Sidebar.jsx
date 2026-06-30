import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

const navItems = [
  { to: '/',             icon: '📊', label: 'Dashboard' },
  { to: '/transactions', icon: '💸', label: 'Transactions' },
  { to: '/upload',       icon: '📥', label: 'Import & Log' },
  { to: '/mappings',     icon: '🔗', label: 'Merchant Mappings' },
  { to: '/budgets',      icon: '🎯', label: 'Budgets' },
  { to: '/goals',        icon: '🏦', label: 'Savings Goals' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="w-64 flex-shrink-0 bg-surface-950 border-r border-surface-700 flex flex-col h-full">
      <div className="px-6 py-5 border-b border-surface-700">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-lg shadow-lg shadow-indigo-500/30">
            💰
          </div>
          <div>
            <div className="font-bold text-white text-base leading-none">FinSense</div>
            <div className="text-xs text-slate-500 mt-0.5">Finance Analytics</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <p className="px-3 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">Menu</p>
        {navItems.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => isActive ? 'nav-link-active' : 'nav-link'}
          >
            <span className="text-base">{icon}</span>
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="px-3 py-4 border-t border-surface-700">
        <div className="flex items-center gap-3 px-3 py-2 mb-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-sm font-bold text-white flex-shrink-0">
            {user?.name?.charAt(0)?.toUpperCase() || 'U'}
          </div>
          <div className="min-w-0">
            <div className="text-sm font-medium text-slate-200 truncate">{user?.name || 'User'}</div>
            <div className="text-xs text-slate-500 truncate">{user?.email || ''}</div>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="btn-ghost w-full justify-center text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10"
        >
          <span>🚪</span> Sign out
        </button>
      </div>
    </aside>
  )
}
