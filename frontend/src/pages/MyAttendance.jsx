import { useEffect, useState } from 'react'

import { getMonthlyAttendance } from '../api/attendance'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import SidebarLayout from '../components/SidebarLayout'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

export default function MyAttendance() {
  const { user } = useAuth()
  const { showToast } = useToast()
  const now = new Date()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user?.employee_id) {
      setLoading(false)
      return
    }
    getMonthlyAttendance(user.employee_id, now.getMonth() + 1, now.getFullYear())
      .then(setData)
      .catch((err) => showToast(err.response?.data?.detail || 'Failed to load attendance', 'error'))
      .finally(() => setLoading(false))
  }, [user, showToast])

  return (
    <SidebarLayout title="My Attendance">
      {loading && <LoadingSpinner />}
      {!loading && !data && <EmptyState title="No attendance records" />}
      {!loading && data && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-xl border bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Present</p>
              <p className="text-2xl font-bold text-blue-700">{data.summary.total_present}</p>
            </div>
            <div className="rounded-xl border bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Absent</p>
              <p className="text-2xl font-bold text-blue-700">{data.summary.total_absent}</p>
            </div>
            <div className="rounded-xl border bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Half Days</p>
              <p className="text-2xl font-bold text-blue-700">{data.summary.total_half_days}</p>
            </div>
          </div>
          <div className="overflow-hidden rounded-xl border bg-white shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left">Date</th>
                  <th className="px-4 py-3 text-left">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {data.records.map((record) => (
                  <tr key={record.id}>
                    <td className="px-4 py-3">{record.date}</td>
                    <td className="px-4 py-3">{record.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </SidebarLayout>
  )
}
