import { useEffect, useState } from 'react'

import { getPayroll } from '../api/payroll'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import SidebarLayout from '../components/SidebarLayout'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { formatCurrency } from '../utils/auth'

export default function MyPayroll() {
  const { user } = useAuth()
  const { showToast } = useToast()
  const now = new Date()
  const [payroll, setPayroll] = useState(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    if (!user?.employee_id) return
    getPayroll(user.employee_id, now.getMonth() + 1, now.getFullYear())
      .then(setPayroll)
      .catch((err) => {
        if (err.response?.status === 404) setNotFound(true)
        else showToast(err.response?.data?.detail || 'Failed to load payroll', 'error')
      })
      .finally(() => setLoading(false))
  }, [user, showToast])

  return (
    <SidebarLayout title="My Payroll">
      {loading && <LoadingSpinner />}
      {!loading && notFound && (
        <EmptyState
          title="Payroll not generated"
          description="Your payroll for this month has not been generated yet."
        />
      )}
      {!loading && payroll && (
        <div className="grid gap-4 sm:grid-cols-2">
          {[
            ['Base Salary', formatCurrency(payroll.base_salary)],
            ['Net Salary', formatCurrency(payroll.net_salary)],
            ['Present Days', payroll.total_present],
            ['Absent Days', payroll.total_absent],
            ['Half Days', payroll.total_half_days],
            ['Deductions', formatCurrency(payroll.total_deductions)],
          ].map(([label, value]) => (
            <div key={label} className="rounded-xl border bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">{label}</p>
              <p className="text-xl font-bold text-blue-700">{value}</p>
            </div>
          ))}
        </div>
      )}
    </SidebarLayout>
  )
}
