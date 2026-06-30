import { useState, useCallback } from 'react'
import { uploadCSV, uploadPDF } from '../api/upload'
import VoiceInput from '../components/VoiceInput'

function DropZone({ onFile, accept, label, icon }) {
  const [drag, setDrag] = useState(false)

  const handleDrop = (e) => {
    e.preventDefault()
    setDrag(false)
    const file = e.dataTransfer.files[0]
    if (file) onFile(file)
  }

  return (
    <label
      className={`flex flex-col items-center justify-center gap-3 p-10 border-2 border-dashed rounded-2xl cursor-pointer transition-all duration-200
        ${drag ? 'border-indigo-500 bg-indigo-500/10' : 'border-surface-600 hover:border-indigo-500/60 hover:bg-surface-700/50'}`}
      onDragOver={e => { e.preventDefault(); setDrag(true) }}
      onDragLeave={() => setDrag(false)}
      onDrop={handleDrop}
    >
      <span className="text-4xl">{icon}</span>
      <div className="text-center">
        <p className="text-slate-200 font-medium">{label}</p>
        <p className="text-slate-500 text-sm mt-1">Drag & drop or click to browse</p>
        <p className="text-slate-600 text-xs mt-1">{accept.toUpperCase()} · Max 10 MB</p>
      </div>
      <input
        type="file"
        className="hidden"
        accept={accept === 'csv' ? '.csv' : '.pdf'}
        onChange={e => e.target.files[0] && onFile(e.target.files[0])}
      />
    </label>
  )
}

function UploadResult({ result }) {
  return (
    <div className="card border-emerald-500/30 bg-emerald-500/5 animate-slide-up">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xl">✅</div>
        <div>
          <div className="font-semibold text-white">Upload Successful</div>
          <div className="text-sm text-slate-400">Source: {result.source?.toUpperCase()}</div>
        </div>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Parsed',        value: result.total_parsed,   color: 'text-blue-400' },
          { label: 'Imported',      value: result.total_imported, color: 'text-emerald-400' },
          { label: 'Categorized',   value: result.categorized,    color: 'text-indigo-400' },
          { label: 'Uncategorized', value: result.uncategorized,  color: 'text-amber-400' },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-surface-700/50 rounded-xl p-3 text-center">
            <div className={`text-2xl font-bold ${color}`}>{value}</div>
            <div className="text-xs text-slate-400 mt-1">{label}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function detectFileType(file) {
  const name = file.name.toLowerCase()
  if (name.endsWith('.csv')) return 'csv'
  if (name.endsWith('.pdf')) return 'pdf'
  return null
}

export default function Upload() {
  const [loading,  setLoading]  = useState(false)
  const [progress, setProgress] = useState(0)
  const [error,    setError]    = useState('')
  const [result,   setResult]   = useState(null)

  const handleUpload = useCallback(async (file) => {
    const fileType = detectFileType(file)

    if (!fileType) {
      setError('Unsupported file type. Please upload a .csv or .pdf file.')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)
    setProgress(0)

    try {
      const fn = fileType === 'csv' ? uploadCSV : uploadPDF
      const data = await fn(file, setProgress)
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please check your file format.')
    } finally {
      setLoading(false)
      setProgress(0)
    }
  }, [])

  return (
    <div className="max-w-7xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h2 className="text-xl font-bold text-white">Import & Log Transactions</h2>
        <p className="text-slate-400 text-sm mt-1">Log transactions by voice, or upload statement files</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Voice Logging Column */}
        <div className="lg:col-span-1 space-y-4 bg-surface-900 border border-surface-800 rounded-2xl p-5">
          <h3 className="text-sm font-semibold text-slate-300">🎙️ Log by Voice</h3>
          <VoiceInput />
        </div>

        {/* File Statement Import Column */}
        <div className="lg:col-span-2 space-y-6">
          <h3 className="text-sm font-semibold text-slate-300">📤 Upload Statement Files</h3>

          {/* Upload zones */}
          {!loading && !result && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <DropZone onFile={handleUpload} accept="csv" label="Bank CSV Statement" icon="📊" />
              <DropZone onFile={handleUpload} accept="pdf" label="Bank PDF Statement" icon="📄" />
            </div>
          )}

          {/* Progress */}
          {loading && (
            <div className="card text-center space-y-4">
              <div className="text-3xl animate-bounce">⬆️</div>
              <p className="text-slate-300 font-medium">Uploading and processing...</p>
              <div className="w-full bg-surface-700 rounded-full h-2">
                <div
                  className="h-2 bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full transition-all duration-300"
                  style={{ width: `${progress || 50}%` }}
                />
              </div>
              <p className="text-slate-400 text-sm">{progress ? `${progress}%` : 'Analyzing...'}</p>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-5 py-4 rounded-xl">
              <p className="font-medium">Upload failed</p>
              <p className="text-sm mt-1">{error}</p>
            </div>
          )}

          {/* Result */}
          {result && (
            <>
              <UploadResult result={result} />
              <button onClick={() => setResult(null)} className="btn-secondary w-full justify-center mt-3">
                Upload another file
              </button>
            </>
          )}

          {/* Instructions */}
          {!loading && !result && (
            <div className="card bg-surface-800/50">
              <h3 className="text-sm font-semibold text-slate-300 mb-3">📋 Auto-Detecting Statement Parser</h3>
              <ul className="space-y-2 text-sm text-slate-400">
                <li className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5">✓</span> 
                  <span>**General CSV Statement:** Auto-detects columns for Date, Description/Narration, and Withdrawals. Works across standard formats including HDFC and ICICI.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5">✓</span> 
                  <span>**General PDF Statement:** Auto-detects headers dynamically to parse standard HDFC NetBanking and other 7-column formats.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-amber-400 mt-0.5">ℹ</span> 
                  <span>Only debit/withdrawal rows are imported (income/credits are skipped).</span>
                </li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
