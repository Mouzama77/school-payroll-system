import { useState } from 'react'
import { Link } from 'react-router-dom'

import { forgotPassword } from '../api/auth'
import { useToast } from '../context/ToastContext'

export default function ForgotPassword() {
  const { showToast } = useToast()
  const [email, setEmail] = useState('')
  const [resetInfo, setResetInfo] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    try {
      const data = await forgotPassword(email)
      setResetInfo(data)
      showToast(data.message)
    } catch (err) {
      showToast(err.response?.data?.detail || 'Request failed', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-slate-100 px-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-lg">
        <h1 className="text-2xl font-bold text-slate-900">Forgot Password</h1>
        <p className="mt-1 text-sm text-slate-500">
          Enter your email to generate a password reset link.
        </p>
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email address"
            className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white"
          >
            {loading ? 'Sending...' : 'Send reset link'}
          </button>
        </form>
        {resetInfo?.reset_url && (
          <div className="mt-4 rounded-lg bg-blue-50 p-3 text-sm text-blue-800">
            <p className="font-medium">Development reset link:</p>
            <a href={resetInfo.reset_url} className="break-all underline">
              {resetInfo.reset_url}
            </a>
          </div>
        )}
        <Link to="/login" className="mt-4 inline-block text-sm font-medium text-blue-600">
          Back to login
        </Link>
      </div>
    </div>
  )
}
