import { useTransactions } from '../hooks/useTransactions'
import { formatCurrency, formatDate, modeLabel, truncate } from '../utils/format'
import TransactionFilters from '../components/Transactions/TransactionFilters'
import { CategoryBadge, PaymentModeBadge, SourceBadge } from '../components/UI/Badge'
import { PageSpinner } from '../components/UI/Spinner'
import EmptyState from '../components/UI/EmptyState'
import ErrorState from '../components/UI/ErrorState'
import { deleteTransaction, createTransaction } from '../api/transactions'
import { listCategories } from '../api/categories'
import { useState, useEffect } from 'react'

function TransactionModal({ open, onClose, onSaved }) {
  const [form, setForm] = useState({
    merchant: '',
    amount: '',
    transaction_date: new Date().toISOString().split('T')[0],
    category_id: '',
    payment_mode: 'upi',
    notes: '',
  })
  const [categories, setCategories] = useState([])
  const [loadingCats, setLoadingCats] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open) return
    setLoadingCats(true)
    listCategories()
      .then(setCategories)
      .catch(err => console.error('Failed to load categories', err))
      .finally(() => setLoadingCats(false))
    
    setForm({
      merchant: '',
      amount: '',
      transaction_date: new Date().toISOString().split('T')[0],
      category_id: '',
      payment_mode: 'upi',
      notes: '',
    })
    setError('')
  }, [open])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.merchant.trim() || !form.amount) {
      setError('Merchant and Amount are required.')
      return
    }
    setSaving(true)
    setError('')
    try {
      await createTransaction({
        merchant: form.merchant.trim(),
        amount: parseFloat(form.amount),
        transaction_date: form.transaction_date,
        category_id: form.category_id || null,
        payment_mode: form.payment_mode,
        source: 'manual',
        notes: form.notes.trim() || null,
      })
      onSaved()
      onClose()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create transaction.')
    } finally {
      setSaving(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
      <div className="bg-surface-900 border border-surface-700 rounded-2xl w-full max-w-md p-6 shadow-2xl animate-slide-up">
        <h2 className="text-lg font-bold text-white mb-5">Add New Transaction</h2>
        
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 text-red-400 p-3 rounded-xl text-sm mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Merchant</label>
            <input
              className="input w-full"
              placeholder="e.g. Starbucks"
              required
              value={form.merchant}
              onChange={e => setForm(f => ({ ...f, merchant: e.target.value }))}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Amount (₹)</label>
              <input
                type="number"
                step="0.01"
                className="input w-full"
                placeholder="250.00"
                required
                min="0.01"
                value={form.amount}
                onChange={e => setForm(f => ({ ...f, amount: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Date</label>
              <input
                type="date"
                className="input w-full"
                required
                value={form.transaction_date}
                onChange={e => setForm(f => ({ ...f, transaction_date: e.target.value }))}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Category</label>
              <select
                className="select w-full"
                value={form.category_id}
                onChange={e => setForm(f => ({ ...f, category_id: e.target.value }))}
                disabled={loadingCats}
              >
                <option value="">Uncategorized</option>
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.category_name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Payment Mode</label>
              <select
                className="select w-full"
                required
                value={form.payment_mode}
                onChange={e => setForm(f => ({ ...f, payment_mode: e.target.value }))}
              >
                <option value="upi">UPI</option>
                <option value="cash">Cash</option>
                <option value="credit_card">Credit Card</option>
                <option value="debit_card">Debit Card</option>
                <option value="net_banking">Net Banking</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Notes (Optional)</label>
            <textarea
              className="input w-full h-20 resize-none py-2"
              placeholder="e.g. coffee with team"
              value={form.notes}
              onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary flex-1 justify-center"
              disabled={saving}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary flex-1 justify-center"
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Transaction'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function Transactions() {
  const { transactions, loading, error, total, filters, refetch, updateFilter, nextPage, prevPage } = useTransactions()
  const [deleting, setDeleting] = useState(null)
  const [showModal, setShowModal] = useState(false)

  const handleDelete = async (id) => {
    if (!confirm('Delete this transaction?')) return
    setDeleting(id)
    try {
      await deleteTransaction(id)
      refetch()
    } catch { alert('Failed to delete') }
    finally { setDeleting(null) }
  }

  const page     = Math.floor(filters.skip / filters.limit) + 1
  const lastPage = Math.ceil(total / filters.limit)

  return (
    <div className="space-y-5 animate-fade-in max-w-7xl mx-auto">

      {/* Header row */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Transactions</h2>
          <p className="text-slate-400 text-sm mt-0.5">{total.toLocaleString('en-IN')} total records</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <span>➕</span> Add Transaction
        </button>
      </div>

      {/* Filters */}
      <div className="card py-4">
        <TransactionFilters filters={filters} onUpdate={updateFilter} />
      </div>

      {/* Table */}
      {loading ? <PageSpinner /> : error ? <ErrorState message={error} onRetry={refetch} /> : (
        <>
          {transactions.length === 0 ? (
            <EmptyState icon="💸" message="No transactions found" subtitle="Try adjusting your filters" />
          ) : (
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th className="th">Date</th>
                    <th className="th">Merchant</th>
                    <th className="th">Category</th>
                    <th className="th">Mode</th>
                    <th className="th">Source</th>
                    <th className="th text-right">Amount</th>
                    <th className="th text-center">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map(txn => (
                    <tr key={txn.id} className="tr-hover">
                      <td className="td text-slate-400 text-xs">{formatDate(txn.transaction_date)}</td>
                      <td className="td">
                        <div className="font-medium text-slate-200">{truncate(txn.merchant, 28)}</div>
                        {txn.notes && <div className="text-xs text-slate-500 mt-0.5 truncate max-w-xs">{txn.notes}</div>}
                      </td>
                      <td className="td">
                        <CategoryBadge name={txn.category?.category_name} />
                      </td>
                      <td className="td">
                        <PaymentModeBadge mode={txn.payment_mode} />
                      </td>
                      <td className="td">
                        <SourceBadge source={txn.source} />
                      </td>
                      <td className="td text-right font-bold text-white tabular-nums">
                        {formatCurrency(txn.amount)}
                      </td>
                      <td className="td text-center">
                        <button
                          onClick={() => handleDelete(txn.id)}
                          disabled={deleting === txn.id}
                          className="btn-danger text-xs px-2 py-1"
                        >
                          {deleting === txn.id ? '...' : '🗑'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {total > filters.limit && (
            <div className="flex items-center justify-between pt-4 border-t border-surface-700">
              <button onClick={prevPage} disabled={filters.skip === 0} className="btn-secondary text-xs">
                ⬅️ Previous
              </button>
              <span className="text-xs text-slate-500 font-medium">
                Page {page} of {lastPage || 1}
              </span>
              <button onClick={nextPage} disabled={filters.skip + filters.limit >= total} className="btn-secondary text-xs">
                Next ➡️
              </button>
            </div>
          )}
        </>
      )}

      {/* Manual add transaction modal */}
      <TransactionModal
        open={showModal}
        onClose={() => setShowModal(false)}
        onSaved={refetch}
      />
    </div>
  )
}
