import { useEffect, useState } from 'react'

import { getReports } from '../api/dashboard'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import SidebarLayout from '../components/SidebarLayout'
import { useToast } from '../context/ToastContext'
import { formatCurrency } from '../utils/auth'

export default function Reports() {
  const { showToast } = useToast()
  const now = new Date()
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [year, setYear] = useState(now.getFullYear())
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)

  const loadReport = async () => {
    setLoading(true)
    try {
      setReport(await getReports(Number(month), Number(year)))
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to load report', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadReport()
  }, [])

  return (
    <SidebarLayout title="Reports">
      <div className="mb-6 flex flex-wrap gap-3">
        <input
          type="number"
          min="1"
          max="12"
          value={month}
          onChange={(e) => setMonth(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
        <input
          type="number"
          min="2000"
          value={year}
          onChange={(e) => setYear(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
        <button
          type="button"
          onClick={loadReport}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white"
        >
          Load Report
        </button>
      </div>

      {loading && <LoadingSpinner />}
      {!loading && report && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-xl border bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Employees</p>
              <p className="text-2xl font-bold text-blue-700">{report.total_employees}</p>
            </div>
            <div className="rounded-xl border bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Payrolls Generated</p>
              <p className="text-2xl font-bold text-blue-700">{report.payrolls_generated}</p>
            </div>
            <div className="rounded-xl border bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">Total Payroll</p>
              <p className="text-2xl font-bold text-blue-700">
                {formatCurrency(report.total_payroll_amount)}
              </p>
            </div>
          </div>

          {report.employees.length === 0 ? (
            <EmptyState title="No report data" />
          ) : (
            <div className="overflow-hidden rounded-xl border bg-white shadow-sm">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-3 text-left">Employee</th>
                    <th className="px-4 py-3 text-left">Present</th>
                    <th className="px-4 py-3 text-left">Absent</th>
                    <th className="px-4 py-3 text-left">Half Days</th>
                    <th className="px-4 py-3 text-left">Net Salary</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {report.employees.map((row) => (
                    <tr key={row.employee_id}>
                      <td className="px-4 py-3">{row.employee_name}</td>
                      <td className="px-4 py-3">{row.present_days}</td>
                      <td className="px-4 py-3">{row.absent_days}</td>
                      <td className="px-4 py-3">{row.half_days}</td>
                      <td className="px-4 py-3">{formatCurrency(row.net_salary)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </SidebarLayout>
  )
}
