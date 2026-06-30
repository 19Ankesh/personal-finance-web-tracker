import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { login as apiLogin, forgotPassword } from '../api/auth'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login }    = useAuth()
  const navigate     = useNavigate()
  const [form,    setForm]    = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')

  // Forgot password flow states
  const [isForgot, setIsForgot] = useState(false)
  const [forgotEmail, setForgotEmail] = useState('')
  const [forgotSuccess, setForgotSuccess] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = await apiLogin(form.email, form.password)
      login(data.access_token, data.user)
      // Use React Router navigate — no full page reload
      navigate('/', { replace: true })
    } catch (err) {
      const detail = err.response?.data?.detail
      if (Array.isArray(detail)) {
        setError(detail.map(d => d.msg || JSON.stringify(d)).join('. '))
      } else {
        setError(typeof detail === 'string' ? detail : 'Invalid email or password')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleForgotSubmit = async (e) => {
    e.preventDefault()
    if (!forgotEmail.trim()) return

    setLoading(true)
    setError('')
    setForgotSuccess(false)
    try {
      await forgotPassword(forgotEmail.trim())
      setForgotSuccess(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to request reset link.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface-900 flex items-center justify-center p-4">
      {/* Background gradient orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-violet-600/20 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md animate-slide-up">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 items-center justify-center text-3xl shadow-2xl shadow-indigo-500/30 mb-4">
            💰
          </div>
          <h1 className="text-3xl font-bold text-white font-sans">
            {isForgot ? 'Recover Account' : 'Welcome back'}
          </h1>
          <p className="text-slate-400 mt-1">
            {isForgot 
              ? 'Request a secure link to reset your password' 
              : 'Sign in to your FinSense account'
            }
          </p>
        </div>

        {/* Card */}
        <div className="card border-surface-700">
          {isForgot ? (
            /* Forgot Password view */
            <form onSubmit={handleForgotSubmit} className="space-y-5">
              {error && (
                <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm px-4 py-3 rounded-xl">
                  {error}
                </div>
              )}

              {forgotSuccess ? (
                <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm px-4 py-3.5 rounded-xl space-y-2">
                  <p className="font-semibold text-white">Reset Link Sent!</p>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    If that email is registered, we've sent instructions to reset your password. Please check your inbox (and verify the backend console log if SMTP is not configured).
                  </p>
                </div>
              ) : (
                <div>
                  <label className="label">Email address</label>
                  <input
                    type="email"
                    className="input"
                    placeholder="you@example.com"
                    value={forgotEmail}
                    onChange={e => setForgotEmail(e.target.value)}
                    required
                    autoFocus
                  />
                </div>
              )}

              <button type="submit" disabled={loading || forgotSuccess} className="btn-primary w-full justify-center py-3 text-base">
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Requesting...
                  </span>
                ) : 'Send Reset Link'}
              </button>

              <div className="text-center text-sm pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setIsForgot(false)
                    setError('')
                    setForgotSuccess(false)
                  }}
                  className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
                >
                  Back to Sign in
                </button>
              </div>
            </form>
          ) : (
            /* Standard Login view */
            <form onSubmit={handleSubmit} className="space-y-5">
              {error && (
                <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm px-4 py-3 rounded-xl">
                  {error}
                </div>
              )}

              <div>
                <label className="label">Email address</label>
                <input
                  type="email"
                  className="input"
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                  required
                  autoFocus
                />
              </div>

              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="label mb-0">Password</label>
                  <button
                    type="button"
                    onClick={() => {
                      setIsForgot(true)
                      setError('')
                    }}
                    className="text-xs text-indigo-400 hover:text-indigo-300 font-medium transition-colors hover:underline"
                  >
                    Forgot password?
                  </button>
                </div>
                <input
                  type="password"
                  className="input"
                  placeholder="••••••••"
                  value={form.password}
                  onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                  required
                />
              </div>

              <button type="submit" disabled={loading} className="btn-primary w-full justify-center py-3 text-base">
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Signing in...
                  </span>
                ) : 'Sign in'}
              </button>

              <div className="mt-5 text-center text-sm text-slate-400">
                Don't have an account?{' '}
                <Link to="/register" className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors">
                  Create one
                </Link>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
