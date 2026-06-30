import { useState, useEffect } from 'react'
import { listMappings, saveMapping, deleteMapping } from '../api/mappings'
import { listCategories } from '../api/categories'
import { PageSpinner } from '../components/UI/Spinner'
import EmptyState from '../components/UI/EmptyState'
import ErrorState from '../components/UI/ErrorState'

export default function Mappings() {
  const [mappings, setMappings] = useState([])
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState('')
  const [form,     setForm]     = useState({ merchant_name: '', category_id: '' })
  const [saving,   setSaving]   = useState(false)
  const [formError, setFormError] = useState('')
  const [deleting, setDeleting] = useState(null)
  const [categories, setCategories] = useState([])

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const [mappingsData, categoriesData] = await Promise.all([
        listMappings(),
        listCategories()
      ])
      setMappings(mappingsData)
      setCategories(categoriesData)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load mappings')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleSave = async (e) => {
    e.preventDefault()
    if (!form.merchant_name.trim() || !form.category_id) {
      setFormError('Both fields are required')
      return
    }
    setSaving(true)
    setFormError('')
    try {
      await saveMapping(form.merchant_name.trim(), form.category_id)
      setForm({ merchant_name: '', category_id: '' })
      await load()
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to save mapping')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this mapping?')) return
    setDeleting(id)
    try {
      await deleteMapping(id)
      setMappings(prev => prev.filter(m => m.id !== id))
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete')
    } finally {
      setDeleting(null) }
  }

  const userMappings   = mappings.filter(m => m.user_id !== null)
  const globalMappings = mappings.filter(m => m.user_id === null)

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h2 className="text-xl font-bold text-white">Merchant Mappings</h2>
        <p className="text-slate-400 text-sm mt-1">
          Teach the system to auto-categorize merchants on future imports
        </p>
      </div>

      {/* Add mapping form */}
      <div className="card">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">➕ Add / Update Mapping</h3>
        <form onSubmit={handleSave} className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-48">
            <label className="label">Merchant name</label>
            <input
              type="text"
              className="input"
              placeholder="e.g. swiggy"
              value={form.merchant_name}
              onChange={e => setForm(f => ({ ...f, merchant_name: e.target.value }))}
            />
          </div>
          <div className="flex-1 min-w-48">
            <label className="label">Category</label>
            <select
              className="select"
              value={form.category_id}
              onChange={e => setForm(f => ({ ...f, category_id: e.target.value }))}
            >
              <option value="">Select category...</option>
              {categories.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.category_name}</option>
              ))}
            </select>
          </div>
          <button type="submit" disabled={saving} className="btn-primary h-[46px]">
            {saving ? 'Saving...' : 'Save Mapping'}
          </button>
        </form>
        {formError && <p className="text-red-400 text-sm mt-2">{formError}</p>}
      </div>

      {loading ? <PageSpinner /> : error ? <ErrorState message={error} onRetry={load} /> : (
        <>
          {/* User mappings */}
          <div>
            <h3 className="text-sm font-semibold text-slate-300 mb-3">
              👤 Your Mappings <span className="badge-indigo ml-2">{userMappings.length}</span>
            </h3>
            {userMappings.length === 0 ? (
              <EmptyState icon="🔗" message="No custom mappings yet" subtitle="Add one above to start auto-categorizing" />
            ) : (
              <div className="table-wrapper">
                <table className="table">
                  <thead>
                    <tr>
                      <th className="th">Merchant</th>
                      <th className="th">Category</th>
                      <th className="th text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {userMappings.map(m => (
                      <tr key={m.id} className="tr-hover">
                        <td className="td font-mono text-slate-300 text-sm">{m.merchant_name}</td>
                        <td className="td">
                          <span className="badge-indigo">{m.category?.category_name || '—'}</span>
                        </td>
                        <td className="td text-center">
                          <button
                            onClick={() => handleDelete(m.id)}
                            disabled={deleting === m.id}
                            className="btn-danger text-xs px-2 py-1"
                          >
                            {deleting === m.id ? '...' : '🗑 Delete'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Global mappings */}
          <div>
            <h3 className="text-sm font-semibold text-slate-300 mb-3">
              🌐 Global Defaults <span className="badge-slate ml-2">{globalMappings.length}</span>
            </h3>
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th className="th">Merchant</th>
                    <th className="th">Category</th>
                    <th className="th text-center">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {globalMappings.map(m => (
                    <tr key={m.id} className="tr-hover opacity-75">
                      <td className="td font-mono text-slate-400 text-sm">{m.merchant_name}</td>
                      <td className="td">
                        <span className="badge-slate">{m.category?.category_name || '—'}</span>
                      </td>
                      <td className="td text-center">
                        <span className="text-xs text-slate-500">🔒 Protected</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
