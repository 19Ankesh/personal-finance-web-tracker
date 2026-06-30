import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { resetPassword } from '../api/auth'

export default function ResetPassword() {
  const navigate = useNavigate()
  const [token, setToken] = useState('')
  const [form, setForm] = useState({ password: '', confirmPassword: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    const queryToken = new URLSearchParams(window.location.search).get('token')
    if (queryToken) {
      setToken(queryToken)
    } else {
      setError('Invalid recovery link. The reset token is missing.')
    }
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!token) return

    if (form.password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }

    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)
    setError('')
    try {
      await resetPassword(token, form.password)
      setSuccess(true)
      setTimeout(() => {
        navigate('/login')
      }, 3000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reset password. The link may have expired.')
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
          <h1 className="text-3xl font-bold text-white font-sans">Reset Password</h1>
          <p className="text-slate-400 mt-1">Set a secure new password for your account</p>
        </div>

        {/* Card */}
        <div className="card border-surface-700">
          {success ? (
            <div className="text-center space-y-4 py-3">
              <span className="text-4xl">🎉</span>
              <h2 className="text-lg font-semibold text-white">Password Reset Successful!</h2>
              <p className="text-slate-400 text-sm">
                Your password has been updated. Redirecting you to the login page...
              </p>
              <Link to="/login" className="btn-primary w-full justify-center">
                Go to Login
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              {error && (
                <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm px-4 py-3 rounded-xl">
                  {error}
                </div>
              )}

              <div>
                <label className="label">New Password</label>
                <input
                  type="password"
                  className="input"
                  placeholder="At least 6 characters"
                  required
                  disabled={!token}
                  value={form.password}
                  onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                />
              </div>

              <div>
                <label className="label">Confirm New Password</label>
                <input
                  type="password"
                  className="input"
                  placeholder="Re-type password"
                  required
                  disabled={!token}
                  value={form.confirmPassword}
                  onChange={e => setForm(f => ({ ...f, confirmPassword: e.target.value }))}
                />
              </div>

              <button
                type="submit"
                disabled={loading || !token}
                className="btn-primary w-full justify-center py-3 text-base"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Resetting...
                  </span>
                ) : 'Reset Password'}
              </button>

              <div className="text-center mt-4">
                <Link to="/login" className="text-sm text-indigo-400 hover:text-indigo-300 font-medium transition-colors">
                  Back to Login
                </Link>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
