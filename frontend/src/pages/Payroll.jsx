import { useEffect, useState } from 'react'

import { getEmployees } from '../api/employees'
import { generatePayroll } from '../api/payroll'
import SidebarLayout from '../components/SidebarLayout'
import { useToast } from '../context/ToastContext'
import { formatCurrency } from '../utils/auth'

function PayrollDetails({ payroll }) {
  const rows = [
    ['Base Salary', formatCurrency(payroll.base_salary)],
    ['Present', payroll.total_present],
    ['Absent', payroll.total_absent],
    ['Half Days', payroll.total_half_days],
    ['Deductions', formatCurrency(payroll.total_deductions)],
    ['Net Salary', formatCurrency(payroll.net_salary)],
  ]

  return (
    <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-lg font-semibold">
        Payroll {payroll.month}/{payroll.year}
      </h2>
      <dl className="grid gap-3 sm:grid-cols-2">
        {rows.map(([label, value]) => (
          <div key={label} className="rounded-lg bg-slate-50 px-4 py-3">
            <dt className="text-xs uppercase text-slate-500">{label}</dt>
            <dd className="mt-1 font-semibold">{value}</dd>
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
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    getEmployees()
      .then((data) => {
        setEmployees(data)
        if (data.length > 0) setEmployeeId(data[0].id)
      })
      .catch((err) => showToast(err.response?.data?.detail || 'Failed to load employees', 'error'))
  }, [showToast])

  const handleGenerate = async (event) => {
    event.preventDefault()
    setLoading(true)
    try {
      const data = await generatePayroll({
        employee_id: employeeId,
        month: Number(month),
        year: Number(year),
      })
      setPayroll(data)
      showToast('Payroll generated')
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to generate payroll', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <SidebarLayout title="Payroll">
      <form onSubmit={handleGenerate} className="max-w-xl space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <select
          required
          value={employeeId}
          onChange={(e) => setEmployeeId(e.target.value)}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          {employees.map((employee) => (
            <option key={employee.id} value={employee.id}>
              {employee.first_name} {employee.last_name}
            </option>
          ))}
        </select>
        <div className="grid gap-4 sm:grid-cols-2">
          <input
            type="number"
            min="1"
            max="12"
            required
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
          <input
            type="number"
            min="2000"
            required
            value={year}
            onChange={(e) => setYear(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white"
        >
          {loading ? 'Generating...' : 'Generate Payroll'}
        </button>
      </form>
      {payroll && <PayrollDetails payroll={payroll} />}
    </SidebarLayout>
  )
}
