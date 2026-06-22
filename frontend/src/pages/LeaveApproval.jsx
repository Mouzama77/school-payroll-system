import { useEffect, useMemo, useState } from 'react'

import { getLeaves, updateLeaveStatus } from '../api/leaves'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import SidebarLayout from '../components/SidebarLayout'
import { useToast } from '../context/ToastContext'

const STATUS_FILTER_OPTIONS = ['ALL', 'PENDING', 'APPROVED', 'REJECTED']

const STATUS_BADGE = {
  PENDING: 'bg-yellow-100 text-yellow-800',
  APPROVED: 'bg-green-100 text-green-800',
  REJECTED: 'bg-red-100 text-red-800',
}

function StatusBadge({ status }) {
  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${STATUS_BADGE[status] ?? 'bg-slate-100 text-slate-600'}`}
    >
      {status}
    </span>
  )
}

export default function LeaveApproval() {
  const { showToast } = useToast()
  const [leaves, setLeaves] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [updatingId, setUpdatingId] = useState('')
  const [filter, setFilter] = useState('PENDING')
  const [selected, setSelected] = useState(new Set())
  const [bulkLoading, setBulkLoading] = useState(false)

  const loadLeaves = () => {
    setLoading(true)
    setError('')
    setSelected(new Set())
    getLeaves()
      .then(setLeaves)
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load leave requests'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadLeaves()
  }, [])

  const filtered = useMemo(
    () => (filter === 'ALL' ? leaves : leaves.filter((l) => l.status === filter)),
    [leaves, filter],
  )

  const pendingFiltered = filtered.filter((l) => l.status === 'PENDING')

  const toggleSelect = (id) =>
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })

  const toggleAll = () => {
    if (selected.size === pendingFiltered.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(pendingFiltered.map((l) => l.id)))
    }
  }

  const handleStatus = async (leaveId, status) => {
    setUpdatingId(leaveId)
    try {
      await updateLeaveStatus(leaveId, status)
      showToast(`Leave ${status.toLowerCase()}`)
      loadLeaves()
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to update leave', 'error')
    } finally {
      setUpdatingId('')
    }
  }

  const handleBulkAction = async (status) => {
    if (selected.size === 0) return
    setBulkLoading(true)
    const ids = [...selected]
    const results = await Promise.allSettled(
      ids.map((id) => updateLeaveStatus(id, status)),
    )
    const failed = results.filter((r) => r.status === 'rejected').length
    const succeeded = results.length - failed
    if (succeeded > 0) showToast(`${succeeded} leave(s) ${status.toLowerCase()}`)
    if (failed > 0) showToast(`${failed} leave(s) failed to update`, 'error')
    loadLeaves()
    setBulkLoading(false)
  }

  return (
    <SidebarLayout title="Leave Approval">
      {/* Filter bar */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        {STATUS_FILTER_OPTIONS.map((opt) => (
          <button
            key={opt}
            type="button"
            onClick={() => { setFilter(opt); setSelected(new Set()) }}
            className={`rounded-full px-3 py-1 text-xs font-semibold ${
              filter === opt
                ? 'bg-blue-600 text-white'
                : 'border border-slate-300 text-slate-600 hover:bg-slate-50'
            }`}
          >
            {opt}
          </button>
        ))}

        {selected.size > 0 && (
          <div className="ml-auto flex gap-2">
            <button
              type="button"
              disabled={bulkLoading}
              onClick={() => handleBulkAction('APPROVED')}
              className="rounded-lg bg-green-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-60"
            >
              {bulkLoading ? '…' : `Approve ${selected.size}`}
            </button>
            <button
              type="button"
              disabled={bulkLoading}
              onClick={() => handleBulkAction('REJECTED')}
              className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-60"
            >
              {bulkLoading ? '…' : `Reject ${selected.size}`}
            </button>
          </div>
        )}
      </div>

      {/* States */}
      {loading && <LoadingSpinner />}
      {!loading && error && (
        <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>
      )}
      {!loading && !error && filtered.length === 0 && (
        <EmptyState
          title="No leave requests"
          description={filter === 'ALL' ? 'No requests found.' : `No ${filter.toLowerCase()} requests.`}
        />
      )}

      {/* Table */}
      {!loading && !error && filtered.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                {filter === 'PENDING' || filter === 'ALL' ? (
                  <th className="w-10 px-4 py-3">
                    <input
                      type="checkbox"
                      checked={pendingFiltered.length > 0 && selected.size === pendingFiltered.length}
                      onChange={toggleAll}
                      className="rounded border-slate-300"
                    />
                  </th>
                ) : <th className="w-10" />}
                <th className="px-4 py-3 text-left font-medium text-slate-600">Employee</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Type</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Dates</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Reason</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Status</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {filtered.map((leave) => (
                <tr key={leave.id} className={selected.has(leave.id) ? 'bg-blue-50' : ''}>
                  <td className="px-4 py-3">
                    {leave.status === 'PENDING' && (
                      <input
                        type="checkbox"
                        checked={selected.has(leave.id)}
                        onChange={() => toggleSelect(leave.id)}
                        className="rounded border-slate-300"
                      />
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-500">
                    {String(leave.employee_id).slice(0, 8)}…
                  </td>
                  <td className="px-4 py-3 font-medium">{leave.leave_type}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-slate-600">
                    {leave.start_date} → {leave.end_date}
                  </td>
                  <td className="max-w-xs truncate px-4 py-3 text-slate-500">
                    {leave.reason || '—'}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={leave.status} />
                  </td>
                  <td className="space-x-2 px-4 py-3">
                    {leave.status === 'PENDING' && (
                      <>
                        <button
                          type="button"
                          disabled={updatingId === leave.id}
                          onClick={() => handleStatus(leave.id, 'APPROVED')}
                          className="rounded-lg bg-green-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-60"
                        >
                          Approve
                        </button>
                        <button
                          type="button"
                          disabled={updatingId === leave.id}
                          onClick={() => handleStatus(leave.id, 'REJECTED')}
                          className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-60"
                        >
                          Reject
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </SidebarLayout>
  )
}
