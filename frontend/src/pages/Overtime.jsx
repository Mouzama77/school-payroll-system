import { useEffect, useState } from 'react'

import { getEmployees } from '../api/employees'
import { createOvertime } from '../api/overtime'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import SidebarLayout from '../components/SidebarLayout'
import { useToast } from '../context/ToastContext'

export default function Overtime() {
  const { showToast } = useToast()
  const [employees, setEmployees] = useState([])
  const [employeeId, setEmployeeId] = useState('')
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [hours, setHours] = useState('')
  const [rateMultiplier, setRateMultiplier] = useState(1.5)
  const [loading, setLoading] = useState(false)
  const [pageLoading, setPageLoading] = useState(true)
  const [created, setCreated] = useState(null)

  useEffect(() => {
    getEmployees()
      .then((data) => {
        setEmployees(data)
        if (data.length > 0) setEmployeeId(data[0].id)
      })
      .catch((err) => showToast(err.response?.data?.detail || 'Failed to load employees', 'error'))
      .finally(() => setPageLoading(false))
  }, [showToast])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!employeeId) return showToast('Select an employee', 'error')
    if (!date) return showToast('Select a date', 'error')
    const hrs = Number(hours)
    if (!hrs || hrs <= 0) return showToast('Hours must be greater than 0', 'error')

    setLoading(true)
    setCreated(null)
    try {
      const payload = {
        employee_id: employeeId,
        date,
        hours: hrs,
        rate_multiplier: Number(rateMultiplier) || 1.5,
      }
      const data = await createOvertime(payload)
      setCreated(data)
      showToast('Overtime record created')
      setHours('')
      setRateMultiplier(1.5)
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to create overtime', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <SidebarLayout title="Overtime">
      {pageLoading && <LoadingSpinner />}

      {!pageLoading && (
        <>
          <form className="max-w-2xl rounded-xl border border-slate-200 bg-white p-6 shadow-sm" onSubmit={handleSubmit}>
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
                <label className="mb-1 block text-xs font-medium text-slate-700">Date</label>
                <input
                  type="date"
                  required
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium text-slate-700">Hours</label>
                <input
                  type="number"
                  step="0.25"
                  min="0.25"
                  required
                  value={hours}
                  onChange={(e) => setHours(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium text-slate-700">Rate Multiplier</label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  required
                  value={rateMultiplier}
                  onChange={(e) => setRateMultiplier(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
            </div>

            <div className="mt-4 flex gap-3">
              <button
                type="submit"
                disabled={loading}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
              >
                {loading ? 'Submitting…' : 'Create Overtime'}
              </button>
            </div>
          </form>

          {created && (
            <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-slate-900">Overtime Created</h3>
              <dl className="mt-3 grid gap-2 sm:grid-cols-2">
                <div className="rounded-lg bg-slate-50 px-4 py-3">
                  <dt className="text-xs font-medium uppercase text-slate-500">Date</dt>
                  <dd className="mt-1 text-sm font-semibold text-slate-900">{created.date}</dd>
                </div>
                <div className="rounded-lg bg-slate-50 px-4 py-3">
                  <dt className="text-xs font-medium uppercase text-slate-500">Hours</dt>
                  <dd className="mt-1 text-sm font-semibold text-slate-900">{created.hours}</dd>
                </div>
                <div className="rounded-lg bg-slate-50 px-4 py-3">
                  <dt className="text-xs font-medium uppercase text-slate-500">Rate Multiplier</dt>
                  <dd className="mt-1 text-sm font-semibold text-slate-900">{created.rate_multiplier}</dd>
                </div>
                <div className="rounded-lg bg-slate-50 px-4 py-3">
                  <dt className="text-xs font-medium uppercase text-slate-500">ID</dt>
                  <dd className="mt-1 text-sm font-mono text-slate-500">{created.id}</dd>
                </div>
              </dl>
            </div>
          )}

          {!created && !loading && employees.length === 0 && (
            <div className="mt-6">
              <EmptyState title="No employees" description="No employees available to assign overtime." />
            </div>
          )}
        </>
      )}
    </SidebarLayout>
  )
}
