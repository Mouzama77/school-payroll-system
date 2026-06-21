import { useEffect, useState } from 'react'

import { getLeaves, updateLeaveStatus } from '../api/leaves'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import SidebarLayout from '../components/SidebarLayout'
import { useToast } from '../context/ToastContext'

export default function LeaveApproval() {
  const { showToast } = useToast()
  const [leaves, setLeaves] = useState([])
  const [loading, setLoading] = useState(true)
  const [updatingId, setUpdatingId] = useState('')

  const loadLeaves = () => {
    setLoading(true)
    getLeaves()
      .then(setLeaves)
      .catch((err) => showToast(err.response?.data?.detail || 'Failed to load leaves', 'error'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadLeaves()
  }, [])

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

  return (
    <SidebarLayout title="Leave Approval">
      {loading && <LoadingSpinner />}
      {!loading && leaves.length === 0 && <EmptyState title="No leave requests" />}
      {!loading && leaves.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Employee</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Type</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Dates</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Status</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {leaves.map((leave) => (
                <tr key={leave.id}>
                  <td className="px-4 py-3 text-slate-600">{leave.employee_id}</td>
                  <td className="px-4 py-3">{leave.leave_type}</td>
                  <td className="px-4 py-3 text-slate-600">
                    {leave.start_date} to {leave.end_date}
                  </td>
                  <td className="px-4 py-3">{leave.status}</td>
                  <td className="space-x-2 px-4 py-3">
                    <button
                      type="button"
                      disabled={updatingId === leave.id}
                      onClick={() => handleStatus(leave.id, 'APPROVED')}
                      className="rounded-lg bg-green-600 px-3 py-1.5 text-xs font-semibold text-white"
                    >
                      Approve
                    </button>
                    <button
                      type="button"
                      disabled={updatingId === leave.id}
                      onClick={() => handleStatus(leave.id, 'REJECTED')}
                      className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-semibold text-white"
                    >
                      Reject
                    </button>
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
