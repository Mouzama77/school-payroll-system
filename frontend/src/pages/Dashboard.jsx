import { useEffect, useState } from 'react'

import { getAuditLogs } from '../api/audit_logs'
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

function formatDatetime(iso) {
  if (!iso) return '—'
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso))
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

const ACTION_BADGE = {
  LEAVE_APPROVED: 'bg-green-100 text-green-800',
  LEAVE_REJECTED: 'bg-red-100 text-red-800',
  ATTENDANCE_OVERRIDDEN: 'bg-blue-100 text-blue-700',
}

function RecentActivity({ logs }) {
  if (!logs || logs.length === 0) {
    return <p className="text-sm text-slate-500">No recent activity.</p>
  }
  return (
    <ul className="space-y-2">
      {logs.map((log) => (
        <li
          key={log.id}
          className="flex items-start gap-3 rounded-lg border border-slate-200 px-3 py-2"
        >
          <span
            className={`mt-0.5 flex-shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold ${ACTION_BADGE[log.action] ?? 'bg-slate-100 text-slate-600'}`}
          >
            {log.action}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm text-slate-700">{log.detail || '—'}</p>
            <p className="text-xs text-slate-400">{formatDatetime(log.created_at)}</p>
          </div>
        </li>
      ))}
    </ul>
  )
}

export default function Dashboard() {
  const { role } = useAuth()
  const [stats, setStats] = useState(null)
  const [leaves, setLeaves] = useState([])
  const [reports, setReports] = useState(null)
  const [recentLogs, setRecentLogs] = useState([])
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
        let logData = []

        if (role === 'admin') {
          ;[data, leaveData, reportData, logData] = await Promise.all([
            getAdminDashboard(),
            getLeaves(),
            getReports(month, year),
            getAuditLogs({ page: 1, page_size: 5 }).catch(() => []),
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
        const items = Array.isArray(logData) ? logData : (logData.items ?? [])
        setRecentLogs(items)
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
        <div className="space-y-6">
          {/* Summary cards */}
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Total Employees" value={stats.total_employees} />
            <StatCard label="Today's Attendance" value={attendanceToday} />
            <StatCard
              label="Pending Leaves"
              value={pendingLeaves}
              hint={pendingLeaves > 0 ? 'Action required' : 'All clear'}
            />
            <StatCard
              label="Payroll This Month"
              value={payrollGenerated}
              hint="Generated payrolls"
            />
          </div>

          {/* Leave + attendance overview */}
          <div className="grid gap-4 lg:grid-cols-2">
            <SummaryPanel title="Leave Requests">
              <div className="grid grid-cols-3 gap-3">
                <MiniMetric label="Pending" value={countByStatus(leaves, 'PENDING')} />
                <MiniMetric label="Approved" value={countByStatus(leaves, 'APPROVED')} />
                <MiniMetric label="Rejected" value={countByStatus(leaves, 'REJECTED')} />
              </div>
              {pendingLeaves > 0 && (
                <p className="mt-3 rounded-lg bg-yellow-50 px-3 py-2 text-xs font-medium text-yellow-800">
                  {pendingLeaves} pending leave request(s) require approval.
                </p>
              )}
            </SummaryPanel>

            <SummaryPanel title="Attendance Overview">
              <div className="grid grid-cols-2 gap-3">
                <MiniMetric
                  label="Present Today"
                  value={stats.attendance_present_today ?? stats.attendance_today ?? '—'}
                />
                <MiniMetric
                  label="Absent Today"
                  value={stats.attendance_absent_today ?? '—'}
                />
              </div>
            </SummaryPanel>
          </div>

          {/* Recent activity — admin only */}
          {role === 'admin' && (
            <SummaryPanel title="Recent Activity">
              <RecentActivity logs={recentLogs} />
            </SummaryPanel>
          )}
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
