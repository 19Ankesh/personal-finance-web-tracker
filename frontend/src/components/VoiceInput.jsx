import { useState, useRef, useCallback, useEffect } from 'react'
import { parseVoiceTransaction, createTransaction } from '../api/transactions'
import { listCategories } from '../api/categories'
import { formatCurrency } from '../utils/format'

// ── Browser support check ─────────────────────────────────────────────────────
const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition || null

// ── Error card ─────────────────────────────────────────────────────────────────
function ErrorCard({ message, onDismiss }) {
  return (
    <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-4 animate-slide-up">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🎙️</span>
          <div>
            <p className="text-red-400 font-semibold text-sm">Could not parse</p>
            <p className="text-slate-300 text-xs mt-0.5">{message}</p>
          </div>
        </div>
        <button onClick={onDismiss} className="text-slate-500 hover:text-slate-300 text-lg leading-none">×</button>
      </div>
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function VoiceInput({ onTransactionLogged }) {
  const [listening,   setListening]   = useState(false)
  const [transcript,  setTranscript]  = useState('')
  const [loading,     setLoading]     = useState(false)
  const [error,       setError]       = useState(null)
  
  // Confirmation / Edit Form State
  const [parsedData,  setParsedData]  = useState(null)
  const [categories,  setCategories]  = useState([])
  const [loadingCats, setLoadingCats] = useState(false)
  const [saving,      setSaving]      = useState(false)
  const [successMsg,  setSuccessMsg]  = useState('')

  const recognitionRef = useRef(null)
  const transcriptRef  = useRef('')

  // Load categories when voice log is parsed
  useEffect(() => {
    if (!parsedData) return
    setLoadingCats(true)
    listCategories()
      .then(setCategories)
      .catch(err => console.error('Failed to load categories', err))
      .finally(() => setLoadingCats(false))
  }, [parsedData])

  // ── Not supported ─────────────────────────────────────────────────────────
  if (!SpeechRecognition) {
    return (
      <div className="card border-amber-500/20 bg-amber-500/5 text-center py-6">
        <p className="text-amber-400 font-medium text-sm">🎙️ Voice input not supported</p>
        <p className="text-slate-500 text-xs mt-1">Use Chrome or Edge on desktop for voice logging.</p>
      </div>
    )
  }

  // ── Start recording ───────────────────────────────────────────────────────
  const startListening = useCallback(() => {
    setParsedData(null)
    setSuccessMsg('')
    setError(null)
    setTranscript('')
    transcriptRef.current = ''

    const recognition = new SpeechRecognition()
    recognition.lang           = 'en-IN'   // Indian English for better UPI merchant names
    recognition.interimResults = true
    recognition.maxAlternatives = 1
    recognitionRef.current = recognition

    recognition.onstart = () => setListening(true)

    recognition.onerror = (event) => {
      setListening(false)
      if (event.error !== 'no-speech') {
        setError(`Microphone error: ${event.error}. Please try again.`)
      }
    }

    recognition.onend = async () => {
      setListening(false)
      const finalText = transcriptRef.current
      if (!finalText.trim()) return

      setLoading(true)
      try {
        const data = await parseVoiceTransaction(finalText)
        if (data.parse_ok) {
          setParsedData({
            merchant:         data.merchant || '',
            amount:           data.amount || '',
            transaction_date: data.transaction_date || new Date().toISOString().split('T')[0],
            category_id:      data.category_id || '',
            payment_mode:     data.payment_mode || 'upi',
            notes:            data.notes || '',
          })
          setTranscript('')
        } else {
          setError(data.error || 'Could not understand the amount. Try saying: "spent 200 on lunch"')
          setTranscript('')
        }
      } catch (e) {
        setError(e.response?.data?.detail || 'Failed to parse voice. Please try again.')
      } finally {
        setLoading(false)
      }
    }

    recognition.onresult = (event) => {
      const text = Array.from(event.results).map(r => r[0].transcript).join(' ')
      setTranscript(text)
      transcriptRef.current = text
    }

    recognition.start()
  }, [])

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop()
  }, [])

  const handleSaveParsed = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await createTransaction({
        merchant:         parsedData.merchant.trim(),
        amount:           parseFloat(parsedData.amount),
        transaction_date: parsedData.transaction_date,
        category_id:      parsedData.category_id || null,
        payment_mode:     parsedData.payment_mode,
        source:           'voice',
        notes:            parsedData.notes.trim() || null,
      })
      setSuccessMsg(`Logged ₹${parsedData.amount} for ${parsedData.merchant}!`)
      setParsedData(null)
      onTransactionLogged?.()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save transaction.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Mic Button & Transcript Card */}
      <div className="card flex flex-col items-center gap-4 py-6">
        <button
          onClick={listening ? stopListening : startListening}
          disabled={loading || saving}
          className={`relative w-16 h-16 rounded-full flex items-center justify-center text-2xl transition-all duration-200 shadow-lg
            ${listening
              ? 'bg-red-500 hover:bg-red-600 shadow-red-500/40 scale-110'
              : loading
                ? 'bg-surface-700 cursor-not-allowed opacity-60'
                : 'bg-indigo-600 hover:bg-indigo-500 shadow-indigo-500/30 hover:scale-105'
            }`}
          aria-label={listening ? 'Stop recording' : 'Start voice logging'}
        >
          {loading ? (
            <span className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            '🎙️'
          )}
          {listening && (
            <span className="absolute inset-0 rounded-full bg-red-500 animate-ping opacity-30" />
          )}
        </button>

        <div className="text-center">
          {listening ? (
            <p className="text-red-400 font-medium text-sm animate-pulse">Listening… tap to stop</p>
          ) : loading ? (
            <p className="text-slate-400 text-sm">Parsing text…</p>
          ) : (
            <div>
              <p className="text-slate-300 font-medium text-sm font-sans">Tap to speak transaction</p>
              <p className="text-slate-500 text-xs mt-1 leading-relaxed">
                e.g., *"spent 350 on Uber yesterday in cash"* or <br />
                *"paid 500 for dinner on June 25th"*
              </p>
            </div>
          )}
        </div>

        {transcript && (
          <div className="w-full bg-surface-700/50 border border-surface-600 rounded-xl px-4 py-3 text-sm text-slate-200 text-center italic min-h-[48px]">
            "{transcript}"
          </div>
        )}
      </div>

      {/* Success banner */}
      {successMsg && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 p-4 rounded-xl text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span>✅</span>
            <span className="font-semibold">{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg('')} className="text-slate-400 hover:text-slate-200">×</button>
        </div>
      )}

      {/* Error banner */}
      {error && (
        <ErrorCard message={error} onDismiss={() => setError(null)} />
      )}

      {/* Interactive Confirmation/Edit Form */}
      {parsedData && (
        <form onSubmit={handleSaveParsed} className="card bg-surface-800/80 border border-indigo-500/30 p-5 space-y-4 animate-slide-up">
          <div className="border-b border-surface-700 pb-2">
            <h4 className="text-sm font-bold text-indigo-400">🎙️ Verify Voice Parsed Fields</h4>
            <p className="text-xs text-slate-500 mt-0.5">Edit any incorrect fields before confirming save</p>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Merchant</label>
            <input
              className="input w-full"
              required
              value={parsedData.merchant}
              onChange={e => setParsedData(p => ({ ...p, merchant: e.target.value }))}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Amount (₹)</label>
              <input
                type="number"
                step="0.01"
                className="input w-full"
                required
                min="0.01"
                value={parsedData.amount}
                onChange={e => setParsedData(p => ({ ...p, amount: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Date</label>
              <input
                type="date"
                className="input w-full"
                required
                value={parsedData.transaction_date}
                onChange={e => setParsedData(p => ({ ...p, transaction_date: e.target.value }))}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Category</label>
              <select
                className="select w-full"
                value={parsedData.category_id}
                onChange={e => setParsedData(p => ({ ...p, category_id: e.target.value }))}
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
                value={parsedData.payment_mode}
                onChange={e => setParsedData(p => ({ ...p, payment_mode: e.target.value }))}
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
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Transcript / Notes</label>
            <input
              className="input w-full text-slate-400 text-xs"
              value={parsedData.notes}
              onChange={e => setParsedData(p => ({ ...p, notes: e.target.value }))}
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={() => setParsedData(null)}
              className="btn-secondary flex-1 justify-center"
              disabled={saving}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary flex-1 justify-center font-semibold"
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Confirm & Save'}
            </button>
          </div>
        </form>
      )}
    </div>
  )
}
