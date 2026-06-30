import { useState, useEffect, useCallback } from 'react'
import { listBudgets, createBudget, updateBudget, deleteBudget } from '../api/budgets'
import { listCategories } from '../api/categories'
import { formatCurrency } from '../utils/format'
import { PageSpinner } from '../components/UI/Spinner'
import ErrorState from '../components/UI/ErrorState'

// ── Utility ───────────────────────────────────────────────────────────────────

function utilizationColor(pct) {
  if (pct >= 100) return { bar: 'bg-red-500',    text: 'text-red-400',    badge: 'bg-red-500/10 text-red-400 border-red-500/20' }
  if (pct >= 80)  return { bar: 'bg-amber-500',  text: 'text-amber-400',  badge: 'bg-amber-500/10 text-amber-400 border-amber-500/20' }
  return              { bar: 'bg-emerald-500', text: 'text-emerald-400', badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' }
}

const MONTHS = [
  'January','February','March','April','May','June',
  'July','August','September','October','November','December',
]

const currentMonth = () => new Date().getMonth() + 1
const currentYear  = () => new Date().getFullYear()

// ── Budget card ───────────────────────────────────────────────────────────────

function BudgetCard({ budget, onEdit, onDelete, deleting }) {
  const pct    = Math.min(budget.utilization_pct ?? 0, 100)
  const colors = utilizationColor(budget.utilization_pct ?? 0)
  const over   = (budget.utilization_pct ?? 0) >= 100

  return (
    <div className="card animate-slide-up space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-white text-base">{budget.category_name}</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            {MONTHS[(budget.month ?? 1) - 1]} {budget.year}
          </p>
        </div>
        <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${colors.badge}`}>
          {over ? 'Over Budget' : `${Math.round(budget.utilization_pct ?? 0)}%`}
        </span>
      </div>

      {/* Progress bar */}
      <div>
        <div className="w-full bg-surface-700 rounded-full h-2">
          <div
            className={`${colors.bar} h-2 rounded-full transition-all duration-500`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <div className="flex justify-between mt-1.5 text-xs text-slate-500">
          <span>Spent: <span className={`font-medium ${colors.text}`}>{formatCurrency(budget.current_spend ?? 0)}</span></span>
          <span>Limit: <span className="font-medium text-slate-300">{formatCurrency(budget.budget_limit)}</span></span>
        </div>
      </div>

      {/* Remaining */}
      <div className="flex items-center justify-between text-sm border-t border-surface-700 pt-3">
        <span className="text-slate-400">Remaining</span>
        <span className={`font-bold tabular-nums ${(budget.remaining ?? 0) < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
          {(budget.remaining ?? 0) < 0 ? '−' : ''}{formatCurrency(Math.abs(budget.remaining ?? 0))}
        </span>
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-1">
        <button onClick={() => onEdit(budget)} className="btn-secondary flex-1 text-xs py-1.5">
          ✏️ Edit
        </button>
        <button
          onClick={() => onDelete(budget.id)}
          disabled={deleting === budget.id}
          className="btn-danger flex-1 text-xs py-1.5"
        >
          {deleting === budget.id ? '...' : '🗑 Delete'}
        </button>
      </div>
    </div>
  )
}

// ── Budget modal ──────────────────────────────────────────────────────────────

function BudgetModal({ open, onClose, onSaved, editing }) {
  const [categories, setCategories] = useState([])
  const [form, setForm] = useState({
    category_id: '',
    budget_limit: '',
    month: currentMonth(),
    year: currentYear(),
  })
  const [saving, setSaving] = useState(false)
  const [error,  setError]  = useState('')

  useEffect(() => {
    if (!open) return

    // Fetch from dedicated /categories/ endpoint — returns ALL categories
    // including ones with no transactions yet (unlike the analytics endpoint)
    listCategories()
      .then(data => setCategories(data))
      .catch(() => setCategories([]))

    if (editing) {
      setForm({
        category_id:  editing.category_id,
        budget_limit: editing.budget_limit,
        month:        editing.month,
        year:         editing.year,
      })
    } else {
      setForm({ category_id: '', budget_limit: '', month: currentMonth(), year: currentYear() })
    }
    setError('')
  }, [open, editing])

  const handleSubmit = async () => {
    if (!form.category_id || !form.budget_limit) {
      setError('Please fill all required fields.')
      return
    }
    setSaving(true)
    setError('')
    try {
      if (editing) {
        await updateBudget(editing.id, { budget_limit: parseFloat(form.budget_limit) })
      } else {
        await createBudget({
          category_id:  form.category_id,
          budget_limit: parseFloat(form.budget_limit),
          month:        parseInt(form.month),
          year:         parseInt(form.year),
        })
      }
      onSaved()
      onClose()
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to save budget.')
    } finally {
      setSaving(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
      <div className="bg-surface-900 border border-surface-700 rounded-2xl w-full max-w-md p-6 shadow-2xl animate-slide-up">
        <h2 className="text-lg font-bold text-white mb-5">
          {editing ? 'Edit Budget Limit' : 'Create Budget'}
        </h2>

        <div className="space-y-4">
          {/* Category — only shown when creating (can't change category on edit) */}
          {!editing && (
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">
                Category <span className="text-red-400">*</span>
              </label>
              <select
                className="select w-full"
                value={form.category_id}
                onChange={e => setForm(f => ({ ...f, category_id: e.target.value }))}
              >
                <option value="">Select a category…</option>
                {categories.map(c => (
                  <option key={c.id} value={c.id}>{c.category_name}</option>
                ))}
              </select>
            </div>
          )}

          {/* Month + Year — only shown when creating */}
          {!editing && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5">Month</label>
                <select
                  className="select w-full"
                  value={form.month}
                  onChange={e => setForm(f => ({ ...f, month: e.target.value }))}
                >
                  {MONTHS.map((m, i) => (
                    <option key={i + 1} value={i + 1}>{m}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5">Year</label>
                <input
                  type="number"
                  className="input w-full"
                  value={form.year}
                  min={2020}
                  max={2030}
                  onChange={e => setForm(f => ({ ...f, year: e.target.value }))}
                />
              </div>
            </div>
          )}

          {/* Budget limit */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">
              Budget Limit (₹) <span className="text-red-400">*</span>
            </label>
            <input
              type="number"
              className="input w-full"
              placeholder="e.g. 5000"
              value={form.budget_limit}
              min={1}
              onChange={e => setForm(f => ({ ...f, budget_limit: e.target.value }))}
            />
          </div>

          {error && <p className="text-red-400 text-xs">{error}</p>}
        </div>

        <div className="flex gap-3 mt-6">
          <button onClick={onClose} className="btn-secondary flex-1">Cancel</button>
          <button onClick={handleSubmit} disabled={saving} className="btn-primary flex-1">
            {saving ? 'Saving…' : editing ? 'Update Limit' : 'Create Budget'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────────

export default function Budgets() {
  const [budgets,     setBudgets]     = useState([])
  const [loading,     setLoading]     = useState(true)
  const [error,       setError]       = useState(null)
  const [modalOpen,   setModal]       = useState(false)
  const [editing,     setEditing]     = useState(null)
  const [deleting,    setDeleting]    = useState(null)
  const [filterMonth, setFilterMonth] = useState(currentMonth())
  const [filterYear,  setFilterYear]  = useState(currentYear())

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await listBudgets({ month: filterMonth, year: filterYear })
      setBudgets(data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load budgets.')
    } finally {
      setLoading(false)
    }
  }, [filterMonth, filterYear])

  useEffect(() => { load() }, [load])

  const handleDelete = async (id) => {
    if (!confirm('Delete this budget?')) return
    setDeleting(id)
    try {
      await deleteBudget(id)
      setBudgets(b => b.filter(x => x.id !== id))
    } catch { alert('Failed to delete budget.') }
    finally { setDeleting(null) }
  }

  const totalBudget = budgets.reduce((s, b) => s + Number(b.budget_limit), 0)
  const totalSpent  = budgets.reduce((s, b) => s + Number(b.current_spend ?? 0), 0)
  const overBudget  = budgets.filter(b => (b.utilization_pct ?? 0) >= 100).length

  return (
    <div className="space-y-6 animate-fade-in max-w-7xl mx-auto">

      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white">Budgets</h2>
          <p className="text-slate-400 text-sm mt-0.5">Track monthly spending limits by category</p>
        </div>
        <button
          onClick={() => { setEditing(null); setModal(true) }}
          className="btn-primary"
        >
          + New Budget
        </button>
      </div>

      {/* Month / Year filter */}
      <div className="flex flex-wrap items-center gap-2">
        <select
          className="select-sm w-36"
          value={filterMonth}
          onChange={e => setFilterMonth(Number(e.target.value))}
        >
          {MONTHS.map((m, i) => <option key={i + 1} value={i + 1}>{m}</option>)}
        </select>
        <input
          type="number"
          className="input-sm w-20"
          value={filterYear}
          min={2020}
          max={2030}
          onChange={e => setFilterYear(Number(e.target.value))}
        />
      </div>

      {/* Summary KPIs */}
      {!loading && budgets.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          <div className="card text-center">
            <p className="text-xs text-slate-400 mb-1">Total Budget</p>
            <p className="text-xl font-bold text-white tabular-nums">{formatCurrency(totalBudget)}</p>
          </div>
          <div className="card text-center">
            <p className="text-xs text-slate-400 mb-1">Total Spent</p>
            <p className="text-xl font-bold text-amber-400 tabular-nums">{formatCurrency(totalSpent)}</p>
          </div>
          <div className="card text-center">
            <p className="text-xs text-slate-400 mb-1">Over Budget</p>
            <p className={`text-xl font-bold tabular-nums ${overBudget > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
              {overBudget} {overBudget === 1 ? 'category' : 'categories'}
            </p>
          </div>
        </div>
      )}

      {/* Content */}
      {loading ? (
        <PageSpinner />
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : budgets.length === 0 ? (
        <div className="card text-center py-14">
          <p className="text-4xl mb-3">🎯</p>
          <p className="text-slate-300 font-medium">No budgets for {MONTHS[filterMonth - 1]} {filterYear}</p>
          <p className="text-slate-500 text-sm mt-1">Create a budget to start tracking your spending limits.</p>
          <button
            onClick={() => { setEditing(null); setModal(true) }}
            className="btn-primary mt-5 mx-auto"
          >
            + Create First Budget
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {budgets.map(b => (
            <BudgetCard
              key={b.id}
              budget={b}
              onEdit={b => { setEditing(b); setModal(true) }}
              onDelete={handleDelete}
              deleting={deleting}
            />
          ))}
        </div>
      )}

      <BudgetModal
        open={modalOpen}
        onClose={() => { setModal(false); setEditing(null) }}
        onSaved={load}
        editing={editing}
      />
    </div>
  )
}
