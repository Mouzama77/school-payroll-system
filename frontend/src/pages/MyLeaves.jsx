import { useEffect, useState } from 'react'

import { createLeaveRequest, getMyLeaves } from '../api/leaves'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import SidebarLayout from '../components/SidebarLayout'
import { useToast } from '../context/ToastContext'

const LEAVE_TYPES = ['CASUAL', 'SICK', 'PAID', 'UNPAID']

export default function MyLeaves() {
  const { showToast } = useToast()
  const [leaves, setLeaves] = useState([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm] = useState({
    leave_type: 'CASUAL',
    start_date: '',
    end_date: '',
    reason: '',
  })

  const loadLeaves = () => {
    setLoading(true)
    getMyLeaves()
      .then(setLeaves)
      .catch((err) => showToast(err.response?.data?.detail || 'Failed to load leaves', 'error'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadLeaves()
  }, [])

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSubmitting(true)
    try {
      await createLeaveRequest({
        ...form,
        reason: form.reason.trim() || null,
      })
      setForm({ leave_type: 'CASUAL', start_date: '', end_date: '', reason: '' })
      showToast('Leave request submitted')
      loadLeaves()
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to submit leave request', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <SidebarLayout title="My Leaves">
      <form
        onSubmit={handleSubmit}
        className="mb-6 max-w-xl space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
      >
        <select
          value={form.leave_type}
          onChange={(e) => setForm({ ...form, leave_type: e.target.value })}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          {LEAVE_TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
        <div className="grid gap-4 sm:grid-cols-2">
          <input
            type="date"
            required
            value={form.start_date}
            onChange={(e) => setForm({ ...form, start_date: e.target.value })}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
          <input
            type="date"
            required
            value={form.end_date}
            onChange={(e) => setForm({ ...form, end_date: e.target.value })}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <textarea
          value={form.reason}
          onChange={(e) => setForm({ ...form, reason: e.target.value })}
          placeholder="Reason"
          className="min-h-24 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={submitting}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white"
        >
          {submitting ? 'Submitting...' : 'Request Leave'}
        </button>
      </form>

      {loading && <LoadingSpinner />}
      {!loading && leaves.length === 0 && <EmptyState title="No leave requests" />}
      {!loading && leaves.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Type</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Dates</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Status</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {leaves.map((leave) => (
                <tr key={leave.id}>
                  <td className="px-4 py-3">{leave.leave_type}</td>
                  <td className="px-4 py-3 text-slate-600">
                    {leave.start_date} to {leave.end_date}
                  </td>
                  <td className="px-4 py-3">{leave.status}</td>
                  <td className="px-4 py-3 text-slate-600">{leave.reason || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </SidebarLayout>
  )
}
