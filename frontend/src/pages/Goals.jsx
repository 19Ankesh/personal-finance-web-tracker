import { useState, useEffect, useCallback } from 'react'
import { listGoals, createGoal, updateGoal, deleteGoal } from '../api/savingsGoals'
import { formatCurrency, formatDate } from '../utils/format'
import { PageSpinner } from '../components/UI/Spinner'
import ErrorState from '../components/UI/ErrorState'

// ── Progress ring ─────────────────────────────────────────────────────────────

function ProgressRing({ pct, size = 72 }) {
  const radius      = (size - 10) / 2
  const circumference = 2 * Math.PI * radius
  const clamped     = Math.min(pct, 100)
  const offset      = circumference - (clamped / 100) * circumference
  const color       = pct >= 100 ? '#10b981' : pct >= 60 ? '#818cf8' : '#fbbf24'

  return (
    <svg width={size} height={size} className="-rotate-90">
      <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#1e293b" strokeWidth={8} />
      <circle
        cx={size / 2} cy={size / 2} r={radius}
        fill="none" stroke={color} strokeWidth={8}
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transition: 'stroke-dashoffset 0.6s ease' }}
      />
    </svg>
  )
}

// ── Days remaining ─────────────────────────────────────────────────────────────

function daysRemaining(targetDate) {
  if (!targetDate) return null
  const diff = Math.ceil((new Date(targetDate) - new Date()) / 86400000)
  return diff
}

// ── Goal card ─────────────────────────────────────────────────────────────────

function GoalCard({ goal, onEdit, onDelete, deleting }) {
  const pct   = goal.progress_percentage
  const days  = daysRemaining(goal.target_date)
  const done  = pct >= 100

  const monthlyRequired = () => {
    if (!goal.target_date || done) return null
    const remaining = Number(goal.target_amount) - Number(goal.current_amount)
    if (remaining <= 0) return null
    const months = Math.max(1, Math.ceil(daysRemaining(goal.target_date) / 30))
    return remaining / months
  }
  const monthly = monthlyRequired()

  return (
    <div className="card animate-slide-up space-y-4">
      {/* Header */}
      <div className="flex items-start gap-4">
        <div className="relative flex-shrink-0">
          <ProgressRing pct={pct} />
          <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-white">
            {Math.round(pct)}%
          </span>
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-white text-base truncate">{goal.goal_name}</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            {done ? (
              <span className="text-emerald-400 font-medium">🎉 Goal reached!</span>
            ) : goal.target_date ? (
              days >= 0
                ? `${days} day${days !== 1 ? 's' : ''} remaining`
                : <span className="text-red-400">Overdue by {Math.abs(days)} days</span>
            ) : 'No deadline set'}
          </p>
        </div>
      </div>

      {/* Amounts */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-surface-800 rounded-xl p-3 text-center">
          <p className="text-xs text-slate-500 mb-0.5">Saved</p>
          <p className="text-sm font-bold text-indigo-400 tabular-nums">{formatCurrency(goal.current_amount)}</p>
        </div>
        <div className="bg-surface-800 rounded-xl p-3 text-center">
          <p className="text-xs text-slate-500 mb-0.5">Target</p>
          <p className="text-sm font-bold text-white tabular-nums">{formatCurrency(goal.target_amount)}</p>
        </div>
      </div>

      {/* Monthly required */}
      {monthly !== null && (
        <div className="flex items-center justify-between text-sm bg-amber-500/5 border border-amber-500/20 rounded-xl px-4 py-2.5">
          <span className="text-slate-400 text-xs">Save/month to reach goal</span>
          <span className="font-bold text-amber-400 tabular-nums text-sm">{formatCurrency(monthly)}</span>
        </div>
      )}

      {/* Target date */}
      {goal.target_date && (
        <p className="text-xs text-slate-500">
          Target date: <span className="text-slate-300">{formatDate(goal.target_date)}</span>
        </p>
      )}

      {/* Actions */}
      <div className="flex gap-2 pt-1 border-t border-surface-700">
        <button onClick={() => onEdit(goal)} className="btn-secondary flex-1 text-xs py-1.5">
          ✏️ Edit
        </button>
        <button
          onClick={() => onDelete(goal.id)}
          disabled={deleting === goal.id}
          className="btn-danger flex-1 text-xs py-1.5"
        >
          {deleting === goal.id ? '...' : '🗑 Delete'}
        </button>
      </div>
    </div>
  )
}

// ── Goal modal ─────────────────────────────────────────────────────────────────

function GoalModal({ open, onClose, onSaved, editing }) {
  const [form, setForm] = useState({
    goal_name: '', target_amount: '', current_amount: '0', target_date: '',
  })
  const [saving, setSaving] = useState(false)
  const [error,  setError]  = useState('')

  useEffect(() => {
    if (!open) return
    if (editing) {
      setForm({
        goal_name:      editing.goal_name,
        target_amount:  editing.target_amount,
        current_amount: editing.current_amount,
        target_date:    editing.target_date || '',
      })
    } else {
      setForm({ goal_name: '', target_amount: '', current_amount: '0', target_date: '' })
    }
    setError('')
  }, [open, editing])

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async () => {
    if (!form.goal_name.trim() || !form.target_amount) {
      setError('Goal name and target amount are required.')
      return
    }
    setSaving(true)
    setError('')
    try {
      const payload = {
        goal_name:      form.goal_name.trim(),
        target_amount:  parseFloat(form.target_amount),
        current_amount: parseFloat(form.current_amount) || 0,
        target_date:    form.target_date || null,
      }
      if (editing) {
        await updateGoal(editing.id, payload)
      } else {
        await createGoal(payload)
      }
      onSaved()
      onClose()
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to save goal.')
    } finally {
      setSaving(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
      <div className="bg-surface-900 border border-surface-700 rounded-2xl w-full max-w-md p-6 shadow-2xl animate-slide-up">
        <h2 className="text-lg font-bold text-white mb-5">
          {editing ? 'Edit Goal' : 'New Savings Goal'}
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Goal Name</label>
            <input className="input w-full" placeholder="e.g. Emergency Fund" value={form.goal_name} onChange={set('goal_name')} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Target Amount (₹)</label>
              <input type="number" className="input w-full" placeholder="50000" min={1} value={form.target_amount} onChange={set('target_amount')} />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Already Saved (₹)</label>
              <input type="number" className="input w-full" placeholder="0" min={0} value={form.current_amount} onChange={set('current_amount')} />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Target Date <span className="text-slate-600">(optional)</span></label>
            <input type="date" className="input w-full" value={form.target_date} onChange={set('target_date')} />
          </div>
          {error && <p className="text-red-400 text-xs">{error}</p>}
        </div>

        <div className="flex gap-3 mt-6">
          <button onClick={onClose} className="btn-secondary flex-1">Cancel</button>
          <button onClick={handleSubmit} disabled={saving} className="btn-primary flex-1">
            {saving ? 'Saving…' : editing ? 'Update' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────────

export default function Goals() {
  const [goals,    setGoals]    = useState([])
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState(null)
  const [modalOpen, setModal]   = useState(false)
  const [editing,  setEditing]  = useState(null)
  const [deleting, setDeleting] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await listGoals()
      setGoals(data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load goals.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleDelete = async (id) => {
    if (!confirm('Delete this savings goal?')) return
    setDeleting(id)
    try {
      await deleteGoal(id)
      setGoals(g => g.filter(x => x.id !== id))
    } catch { alert('Failed to delete goal.') }
    finally { setDeleting(null) }
  }

  const totalSaved  = goals.reduce((s, g) => s + Number(g.current_amount), 0)
  const totalTarget = goals.reduce((s, g) => s + Number(g.target_amount), 0)
  const completed   = goals.filter(g => g.progress_percentage >= 100).length

  return (
    <div className="space-y-6 animate-fade-in max-w-7xl mx-auto">

      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white">Savings Goals</h2>
          <p className="text-slate-400 text-sm mt-0.5">Track your financial targets and progress</p>
        </div>
        <button onClick={() => { setEditing(null); setModal(true) }} className="btn-primary">
          + New Goal
        </button>
      </div>

      {/* Summary KPIs */}
      {!loading && goals.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          <div className="card text-center">
            <p className="text-xs text-slate-400 mb-1">Total Saved</p>
            <p className="text-xl font-bold text-indigo-400 tabular-nums">{formatCurrency(totalSaved)}</p>
          </div>
          <div className="card text-center">
            <p className="text-xs text-slate-400 mb-1">Total Target</p>
            <p className="text-xl font-bold text-white tabular-nums">{formatCurrency(totalTarget)}</p>
          </div>
          <div className="card text-center">
            <p className="text-xs text-slate-400 mb-1">Completed</p>
            <p className={`text-xl font-bold tabular-nums ${completed > 0 ? 'text-emerald-400' : 'text-slate-400'}`}>
              {completed} / {goals.length}
            </p>
          </div>
        </div>
      )}

      {/* Content */}
      {loading ? (
        <PageSpinner />
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : goals.length === 0 ? (
        <div className="card text-center py-14">
          <p className="text-4xl mb-3">🏦</p>
          <p className="text-slate-300 font-medium">No savings goals yet</p>
          <p className="text-slate-500 text-sm mt-1">Set a target and track your progress toward it.</p>
          <button
            onClick={() => { setEditing(null); setModal(true) }}
            className="btn-primary mt-5 mx-auto"
          >
            + Create First Goal
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {goals.map(g => (
            <GoalCard
              key={g.id}
              goal={g}
              onEdit={(g) => { setEditing(g); setModal(true) }}
              onDelete={handleDelete}
              deleting={deleting}
            />
          ))}
        </div>
      )}

      <GoalModal
        open={modalOpen}
        onClose={() => { setModal(false); setEditing(null) }}
        onSaved={load}
        editing={editing}
      />
    </div>
  )
}
