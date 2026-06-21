import { useEffect, useState } from 'react'

import { markAttendance } from '../api/attendance'
import { getEmployees } from '../api/employees'
import LoadingSpinner from '../components/LoadingSpinner'
import SidebarLayout from '../components/SidebarLayout'
import { useToast } from '../context/ToastContext'

const STATUS_OPTIONS = ['PRESENT', 'ABSENT', 'HALF_DAY']

export default function Attendance() {
  const { showToast } = useToast()
  const [employees, setEmployees] = useState([])
  const [employeeId, setEmployeeId] = useState('')
  const [date, setDate] = useState('')
  const [status, setStatus] = useState('PRESENT')
  const [loading, setLoading] = useState(false)
  const [pageLoading, setPageLoading] = useState(true)

  useEffect(() => {
    getEmployees()
      .then((data) => {
        setEmployees(data)
        if (data.length > 0) setEmployeeId(data[0].id)
      })
      .catch((err) => showToast(err.response?.data?.detail || 'Failed to load employees', 'error'))
      .finally(() => setPageLoading(false))
  }, [showToast])

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    try {
      await markAttendance({ employee_id: employeeId, date, status })
      showToast('Attendance marked successfully')
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to mark attendance', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <SidebarLayout title="Attendance">
      {pageLoading && <LoadingSpinner />}
      {!pageLoading && (
        <form onSubmit={handleSubmit} className="max-w-xl space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
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
          <input
            type="date"
            required
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option.replace('_', ' ')}
              </option>
            ))}
          </select>
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white"
          >
            {loading ? 'Submitting...' : 'Submit Attendance'}
          </button>
        </form>
      )}
    </SidebarLayout>
  )
}
