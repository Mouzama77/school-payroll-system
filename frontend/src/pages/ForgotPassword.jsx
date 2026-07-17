import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { forgotPassword, resetPasswordWithOtp, verifyOtp } from '../api/auth'
import { useToast } from '../context/ToastContext'

const STEP = { EMAIL: 'email', OTP: 'otp', RESET: 'reset' }

export default function ForgotPassword() {
  const { showToast } = useToast()
  const navigate = useNavigate()

  const [step, setStep] = useState(STEP.EMAIL)
  const [email, setEmail] = useState('')
  const [otp, setOtp] = useState('')
  const [resetToken, setResetToken] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [loading, setLoading] = useState(false)
  const [cooldown, setCooldown] = useState(0)

  useEffect(() => {
    if (cooldown <= 0) return undefined
    const timer = setInterval(() => setCooldown((c) => Math.max(c - 1, 0)), 1000)
    return () => clearInterval(timer)
  }, [cooldown])

  const requestOtp = async () => {
    setLoading(true)
    try {
      const data = await forgotPassword(email)
      showToast(data.message || 'Verification code sent')
      setStep(STEP.OTP)
      setCooldown(60)
    } catch (err) {
      showToast(err.response?.data?.detail || 'Request failed', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleEmailSubmit = (e) => {
    e.preventDefault()
    requestOtp()
  }

  const handleOtpSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const data = await verifyOtp(email, otp.trim())
      setResetToken(data.reset_token)
      showToast('Code verified')
      setStep(STEP.RESET)
    } catch (err) {
      showToast(err.response?.data?.detail || 'Invalid code', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleResetSubmit = async (e) => {
    e.preventDefault()
    if (password !== confirm) {
      showToast('Passwords do not match', 'error')
      return
    }
    setLoading(true)
    try {
      await resetPasswordWithOtp(email, resetToken, password)
      showToast('Password reset successfully. Please sign in.')
      navigate('/login')
    } catch (err) {
      showToast(err.response?.data?.detail || 'Reset failed', 'error')
    } finally {
      setLoading(false)
    }
  }

  const inputCls =
    'w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500'
  const btnCls =
    'w-full rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-60'

  const stepIndex = step === STEP.EMAIL ? 0 : step === STEP.OTP ? 1 : 2

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-slate-100 px-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-lg">
        <h1 className="text-2xl font-bold text-slate-900">Forgot Password</h1>

        {/* Step indicator */}
        <div className="mt-4 flex items-center gap-2">
          {['Email', 'Verify', 'Reset'].map((label, i) => (
            <div key={label} className="flex flex-1 items-center gap-2">
              <span
                className={`flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                  i <= stepIndex
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-200 text-slate-500'
                }`}
              >
                {i + 1}
              </span>
              <span
                className={`text-xs ${i <= stepIndex ? 'text-slate-900' : 'text-slate-400'}`}
              >
                {label}
              </span>
            </div>
          ))}
        </div>

        {step === STEP.EMAIL && (
          <form onSubmit={handleEmailSubmit} className="mt-6 space-y-4">
            <p className="text-sm text-slate-500">
              Enter your email and we&apos;ll send you a 6-digit verification code.
            </p>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email address"
              className={inputCls}
            />
            <button type="submit" disabled={loading} className={btnCls}>
              {loading ? 'Sending…' : 'Send verification code'}
            </button>
          </form>
        )}

        {step === STEP.OTP && (
          <form onSubmit={handleOtpSubmit} className="mt-6 space-y-4">
            <p className="text-sm text-slate-500">
              Enter the 6-digit code sent to{' '}
              <span className="font-medium text-slate-700">{email}</span>. It
              expires in 10 minutes.
            </p>
            <input
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              required
              maxLength={6}
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
              placeholder="______"
              className={`${inputCls} text-center text-2xl tracking-[0.5em]`}
            />
            <button type="submit" disabled={loading} className={btnCls}>
              {loading ? 'Verifying…' : 'Verify code'}
            </button>
            <button
              type="button"
              disabled={cooldown > 0 || loading}
              onClick={requestOtp}
              className="w-full text-sm font-medium text-blue-600 disabled:text-slate-400"
            >
              {cooldown > 0 ? `Resend code in ${cooldown}s` : 'Resend code'}
            </button>
          </form>
        )}

        {step === STEP.RESET && (
          <form onSubmit={handleResetSubmit} className="mt-6 space-y-4">
            <p className="text-sm text-slate-500">Choose a new password.</p>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="New password (min 8 characters)"
              className={inputCls}
            />
            <input
              type="password"
              required
              minLength={8}
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              placeholder="Confirm new password"
              className={inputCls}
            />
            <button type="submit" disabled={loading} className={btnCls}>
              {loading ? 'Resetting…' : 'Reset password'}
            </button>
          </form>
        )}

        <Link
          to="/login"
          className="mt-6 inline-block text-sm font-medium text-blue-600"
        >
          Back to login
        </Link>
      </div>
    </div>
  )
}
