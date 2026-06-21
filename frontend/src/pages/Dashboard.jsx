import { useEffect, useState } from 'react'

import {
  getAdminDashboard,
  getEmployeeDashboard,
  getHRDashboard,
  getReports,
} from '../api/dashboard'
import { getLeaves, getMyLeaves } from '../api/leaves'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import SidebarLayout from '../components/SidebarLayout'
import StatCard from '../components/StatCard'
import { useAuth } from '../context/AuthContext'
import { formatCurrency } from '../utils/auth'

function getCurrentMonthYear() {
  const today = new Date()
  return {
    month: today.getMonth() + 1,
    year: today.getFullYear(),
  }
}

function countByStatus(leaves, status) {
  return leaves.filter((leave) => leave.status === status).length
}

function getUpcomingApprovedLeaves(leaves) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  return leaves
    .filter((leave) => leave.status === 'APPROVED')
    .filter((leave) => new Date(leave.start_date) >= today)
    .sort((a, b) => new Date(a.start_date) - new Date(b.start_date))
    .slice(0, 3)
}

function formatDate(value) {
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date(value))
}

function SummaryPanel({ title, children }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-base font-semibold text-slate-900">{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  )
}

function MiniMetric({ label, value }) {
  return (
    <div className="rounded-lg bg-slate-50 px-4 py-3">
      <p className="text-xs font-medium uppercase text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-blue-700">{value}</p>
    </div>
  )
}

export default function Dashboard() {
  const { role } = useAuth()
  const [stats, setStats] = useState(null)
  const [leaves, setLeaves] = useState([])
  const [reports, setReports] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        setError('')
        const { month, year } = getCurrentMonthYear()
        let data
        let leaveData = []
        let reportData = null

        if (role === 'admin') {
          ;[data, leaveData, reportData] = await Promise.all([
            getAdminDashboard(),
            getLeaves(),
            getReports(month, year),
          ])
        } else if (role === 'hr') {
          ;[data, leaveData, reportData] = await Promise.all([
            getHRDashboard(),
            getLeaves(),
            getReports(month, year),
          ])
        } else {
          ;[data, leaveData] = await Promise.all([
            getEmployeeDashboard(),
            getMyLeaves(),
          ])
        }

        setStats(data)
        setLeaves(leaveData)
        setReports(reportData)
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load dashboard')
      } finally {
        setLoading(false)
      }
    }
    if (role) load()
  }, [role])

  const pendingLeaves = countByStatus(leaves, 'PENDING')
  const upcomingLeaves = getUpcomingApprovedLeaves(leaves)
  const attendanceToday =
    role === 'admin'
      ? stats?.attendance_today
      : (stats?.attendance_present_today || 0) + (stats?.attendance_absent_today || 0)
  const payrollGenerated =
    stats?.payroll_generated_this_month ?? reports?.payrolls_generated ?? 0

  return (
    <SidebarLayout title="Dashboard">
      {loading && <LoadingSpinner />}
      {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      {!loading && !error && ['admin', 'hr'].includes(role) && stats && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Total Employees" value={stats.total_employees} />
          <StatCard label="Today's Attendance" value={attendanceToday} />
          <StatCard label="Pending Leaves" value={pendingLeaves} />
          <StatCard label="Payroll This Month" value={payrollGenerated} />
        </div>
      )}

      {!loading && !error && role === 'employee' && stats && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label="Attendance %"
              value={`${stats.attendance_percentage}%`}
              hint={`${stats.present_days} of ${stats.total_working_days} days`}
            />
            <StatCard label="Present Days" value={stats.present_days} />
            <StatCard
              label="Latest Payroll"
              value={formatCurrency(stats.net_salary)}
              hint={stats.payroll_status || 'Payroll not generated yet'}
            />
            <StatCard label="Pending Leaves" value={countByStatus(leaves, 'PENDING')} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <SummaryPanel title="Leave Balance Summary">
              {leaves.length === 0 ? (
                <p className="text-sm text-slate-500">No leave requests found.</p>
              ) : (
                <div className="grid gap-3 sm:grid-cols-3">
                  <MiniMetric label="Approved" value={countByStatus(leaves, 'APPROVED')} />
                  <MiniMetric label="Pending" value={countByStatus(leaves, 'PENDING')} />
                  <MiniMetric label="Rejected" value={countByStatus(leaves, 'REJECTED')} />
                </div>
              )}
            </SummaryPanel>

            <SummaryPanel title="Upcoming Approved Leaves">
              {upcomingLeaves.length === 0 ? (
                <p className="text-sm text-slate-500">No upcoming approved leaves.</p>
              ) : (
                <div className="space-y-3">
                  {upcomingLeaves.map((leave) => (
                    <div
                      key={leave.id}
                      className="rounded-lg border border-slate-200 px-4 py-3"
                    >
                      <p className="text-sm font-semibold text-slate-900">
                        {leave.leave_type}
                      </p>
                      <p className="mt-1 text-sm text-slate-600">
                        {formatDate(leave.start_date)} to {formatDate(leave.end_date)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </SummaryPanel>
          </div>
        </div>
      )}

      {!loading && !error && !stats && (
        <EmptyState title="No dashboard data" description="Try again later." />
      )}
    </SidebarLayout>
  )
}
