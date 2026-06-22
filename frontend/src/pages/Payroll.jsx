import { useEffect, useState } from 'react'

import { getEmployees } from '../api/employees'
import { generatePayroll, getPayroll, recalculatePayroll } from '../api/payroll'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import SidebarLayout from '../components/SidebarLayout'
import { useToast } from '../context/ToastContext'
import { formatCurrency } from '../utils/auth'

const STATUS_BADGE = {
  generated: 'bg-green-100 text-green-800',
  recalculated: 'bg-blue-100 text-blue-700',
  pending: 'bg-yellow-100 text-yellow-800',
}

function PayrollDetails({ payroll, onRecalculate, recalcLoading }) {
  const rows = [
    ['Base Salary', formatCurrency(payroll.base_salary)],
    ['Present Days', payroll.total_present],
    ['Absent Days', payroll.total_absent],
    ['Half Days', payroll.total_half_days],
    ['Deductions', formatCurrency(payroll.total_deductions)],
    ['Net Salary', formatCurrency(payroll.net_salary)],
  ]

  return (
    <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-slate-900">
          Payroll {payroll.month}/{payroll.year}
        </h2>
        <div className="flex items-center gap-3">
          <span
            className={`rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ${STATUS_BADGE[payroll.status] ?? 'bg-slate-100 text-slate-600'}`}
          >
            {payroll.status}
          </span>
          <button
            type="button"
            disabled={recalcLoading}
            onClick={onRecalculate}
            className="rounded-lg border border-blue-300 bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-700 hover:bg-blue-100 disabled:opacity-60"
          >
            {recalcLoading ? 'Recalculating…' : '↻ Recalculate Payroll'}
          </button>
        </div>
      </div>
      <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {rows.map(([label, value]) => (
          <div key={label} className="rounded-lg bg-slate-50 px-4 py-3">
            <dt className="text-xs font-medium uppercase text-slate-500">{label}</dt>
            <dd className="mt-1 text-xl font-bold text-blue-700">{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}

export default function Payroll() {
  const { showToast } = useToast()
  const now = new Date()
  const [employees, setEmployees] = useState([])
  const [employeeId, setEmployeeId] = useState('')
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [year, setYear] = useState(now.getFullYear())
  const [payroll, setPayroll] = useState(null)
  const [generateLoading, setGenerateLoading] = useState(false)
  const [recalcLoading, setRecalcLoading] = useState(false)
  const [pageLoading, setPageLoading] = useState(true)

  useEffect(() => {
    getEmployees()
      .then((data) => {
        setEmployees(data)
        if (data.length > 0) setEmployeeId(data[0].id)
      })
      .catch((err) =>
        showToast(err.response?.data?.detail || 'Failed to load employees', 'error'),
      )
      .finally(() => setPageLoading(false))
  }, [showToast])

  const handleGenerate = async (e) => {
    e.preventDefault()
    setGenerateLoading(true)
    setPayroll(null)
    try {
      const data = await generatePayroll({
        employee_id: employeeId,
        month: Number(month),
        year: Number(year),
      })
      setPayroll(data)
      showToast('Payroll generated successfully')
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to generate payroll', 'error')
    } finally {
      setGenerateLoading(false)
    }
  }

  const handleView = async (e) => {
    e.preventDefault()
    setGenerateLoading(true)
    setPayroll(null)
    try {
      const data = await getPayroll(employeeId, Number(month), Number(year))
      setPayroll(data)
    } catch (err) {
      showToast(err.response?.data?.detail || 'Payroll not found for this period', 'error')
    } finally {
      setGenerateLoading(false)
    }
  }

  const handleRecalculate = async () => {
    if (!payroll) return
    setRecalcLoading(true)
    try {
      const data = await recalculatePayroll(payroll.employee_id, payroll.month, payroll.year)
      setPayroll(data)
      showToast('Payroll recalculated using latest attendance data')
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to recalculate payroll', 'error')
    } finally {
      setRecalcLoading(false)
    }
  }

  return (
    <SidebarLayout title="Payroll">
      {pageLoading && <LoadingSpinner />}

      {!pageLoading && (
        <>
          <form className="max-w-2xl rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label className="mb-1 block text-xs font-medium text-slate-700">Employee</label>
                <select
                  required
                  value={employeeId}
                  onChange={(e) => setEmployeeId(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                >
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.first_name} {emp.last_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-700">Month</label>
                <input
                  type="number"
                  min="1"
                  max="12"
                  required
                  value={month}
                  onChange={(e) => setMonth(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-700">Year</label>
                <input
                  type="number"
                  min="2000"
                  required
                  value={year}
                  onChange={(e) => setYear(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
            </div>
            <div className="mt-4 flex flex-wrap gap-3">
              <button
                type="button"
                disabled={generateLoading}
                onClick={handleView}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60"
              >
                {generateLoading ? 'Loading…' : 'View Payroll'}
              </button>
              <button
                type="button"
                disabled={generateLoading}
                onClick={handleGenerate}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
              >
                {generateLoading ? 'Generating…' : 'Generate Payroll'}
              </button>
            </div>
          </form>

          {payroll ? (
            <PayrollDetails
              payroll={payroll}
              onRecalculate={handleRecalculate}
              recalcLoading={recalcLoading}
            />
          ) : (
            !generateLoading && (
              <div className="mt-6">
                <EmptyState
                  title="No payroll loaded"
                  description="Select an employee and period, then click View or Generate."
                />
              </div>
            )
          )}
        </>
      )}
    </SidebarLayout>
  )
}
