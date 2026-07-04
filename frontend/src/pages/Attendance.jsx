import { useEffect, useState } from 'react'

import { getMonthlyAttendance, markAttendance, overrideAttendance } from '../api/attendance'
import { getEmployees } from '../api/employees'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import SidebarLayout from '../components/SidebarLayout'
import { useToast } from '../context/ToastContext'

const MARK_STATUS_OPTIONS = ['PRESENT', 'ABSENT', 'HALF_DAY', 'LATE']
const OVERRIDE_STATUS_OPTIONS = ['PRESENT', 'ABSENT', 'HALF_DAY', 'LATE']

const STATUS_BADGE = {
  PRESENT: 'bg-green-100 text-green-800',
  ABSENT: 'bg-red-100 text-red-800',
  HALF_DAY: 'bg-yellow-100 text-yellow-800',
  ON_LEAVE: 'bg-blue-100 text-blue-700',
  LATE: 'bg-orange-100 text-orange-800',
}

function StatusBadge({ status, isOverride }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className={`rounded-full px-2 py-0.5 text-xs font-semibold ${STATUS_BADGE[status] ?? 'bg-slate-100 text-slate-600'}`}
      >
        {status.replace('_', ' ')}
      </span>
      {isOverride && (
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">
          overridden
        </span>
      )}
    </span>
  )
}

function OverrideModal({ record, onClose, onSuccess }) {
  const { showToast } = useToast()
  const [overrideStatus, setOverrideStatus] = useState('PRESENT')
  const [reason, setReason] = useState('')
  const [loading, setLoading] = useState(false)
  const [reasonError, setReasonError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!reason.trim()) {
      setReasonError('Override reason is required.')
      return
    }
    setReasonError('')
    setLoading(true)
    try {
      const updated = await overrideAttendance(record.id, overrideStatus, reason.trim())
      showToast('Attendance overridden successfully')
      onSuccess(updated)
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to override attendance', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-slate-900">Override Attendance</h3>
        <p className="mt-1 text-sm text-slate-500">
          {record.date} — current status:{' '}
          <span className="font-medium">{record.status}</span>
        </p>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-700">
              New status
            </label>
            <select
              value={overrideStatus}
              onChange={(e) => setOverrideStatus(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            >
              {OVERRIDE_STATUS_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>
                  {opt.replace('_', ' ')}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-slate-700">
              Reason <span className="text-red-500">*</span>
            </label>
            <textarea
              value={reason}
              onChange={(e) => {
                setReason(e.target.value)
                if (e.target.value.trim()) setReasonError('')
              }}
              rows={3}
              placeholder="Mandatory reason for override…"
              className={`w-full rounded-lg border px-3 py-2 text-sm ${
                reasonError ? 'border-red-400 focus:ring-red-300' : 'border-slate-300'
              }`}
            />
            {reasonError && (
              <p className="mt-1 text-xs text-red-600">{reasonError}</p>
            )}
          </div>

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
            >
              {loading ? 'Saving…' : 'Save Override'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function Attendance() {
  const { showToast } = useToast()
  const now = new Date()

  // Mark attendance form
  const [employees, setEmployees] = useState([])
  const [employeeId, setEmployeeId] = useState('')
  const [markDate, setMarkDate] = useState('')
  const [markStatus, setMarkStatus] = useState('PRESENT')
  const [checkInTime, setCheckInTime] = useState('')
  const [markLoading, setMarkLoading] = useState(false)

  // Records panel
  const [viewEmployeeId, setViewEmployeeId] = useState('')
  const [viewMonth, setViewMonth] = useState(now.getMonth() + 1)
  const [viewYear, setViewYear] = useState(now.getFullYear())
  const [records, setRecords] = useState(null)
  const [recordsLoading, setRecordsLoading] = useState(false)
  const [recordsError, setRecordsError] = useState('')

  // Override modal
  const [overrideRecord, setOverrideRecord] = useState(null)

  const [pageLoading, setPageLoading] = useState(true)

  useEffect(() => {
    getEmployees()
      .then((data) => {
        setEmployees(data)
        if (data.length > 0) {
          setEmployeeId(data[0].id)
          setViewEmployeeId(data[0].id)
        }
      })
      .catch((err) =>
        showToast(err.response?.data?.detail || 'Failed to load employees', 'error'),
      )
      .finally(() => setPageLoading(false))
  }, [showToast])

  const handleMarkSubmit = async (e) => {
    e.preventDefault()
    setMarkLoading(true)
    try {
      const payload = { employee_id: employeeId, date: markDate, status: markStatus }
      if (markStatus === 'LATE' && checkInTime) {
        payload.check_in_time = checkInTime
      }
      await markAttendance(payload)
      showToast('Attendance marked successfully')
      setMarkDate('')
      setCheckInTime('')
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to mark attendance', 'error')
    } finally {
      setMarkLoading(false)
    }
  }

  const loadRecords = async () => {
    if (!viewEmployeeId) return
    setRecordsLoading(true)
    setRecordsError('')
    try {
      const data = await getMonthlyAttendance(viewEmployeeId, viewMonth, viewYear)
      setRecords(data)
    } catch (err) {
      setRecordsError(err.response?.data?.detail || 'Failed to load attendance records')
    } finally {
      setRecordsLoading(false)
    }
  }

  const handleOverrideSuccess = (updated) => {
    setOverrideRecord(null)
    setRecords((prev) => {
      if (!prev) return prev
      return {
        ...prev,
        records: prev.records.map((r) => (r.id === updated.id ? updated : r)),
      }
    })
  }

  return (
    <SidebarLayout title="Attendance">
      {pageLoading && <LoadingSpinner />}

      {!pageLoading && (
        <div className="space-y-8">
          {/* Mark attendance */}
          <section>
            <h2 className="mb-3 text-base font-semibold text-slate-900">Mark Attendance</h2>
            <form
              onSubmit={handleMarkSubmit}
              className="grid max-w-2xl gap-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm sm:grid-cols-2"
            >
              <select
                required
                value={employeeId}
                onChange={(e) => setEmployeeId(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm sm:col-span-2"
              >
                {employees.map((emp) => (
                  <option key={emp.id} value={emp.id}>
                    {emp.first_name} {emp.last_name}
                  </option>
                ))}
              </select>
              <input
                type="date"
                required
                value={markDate}
                onChange={(e) => setMarkDate(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
              <select
                value={markStatus}
                onChange={(e) => {
                  setMarkStatus(e.target.value)
                  if (e.target.value !== 'LATE') setCheckInTime('')
                }}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              >
                {MARK_STATUS_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt.replace('_', ' ')}
                  </option>
                ))}
              </select>
              {markStatus === 'LATE' && (
                <div className="sm:col-span-2">
                  <label className="mb-1 block text-xs font-medium text-slate-700">
                    Check-in time <span className="text-slate-400">(optional — used for deduction calculation)</span>
                  </label>
                  <input
                    type="time"
                    value={checkInTime}
                    onChange={(e) => setCheckInTime(e.target.value)}
                    className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
              )}
              <button
                type="submit"
                disabled={markLoading}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60 sm:col-span-2"
              >
                {markLoading ? 'Submitting…' : 'Submit Attendance'}
              </button>
            </form>
          </section>

          {/* View & override records */}
          <section>
            <h2 className="mb-3 text-base font-semibold text-slate-900">
              Monthly Records &amp; Overrides
            </h2>
            <div className="mb-4 flex flex-wrap gap-3">
              <select
                value={viewEmployeeId}
                onChange={(e) => setViewEmployeeId(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
              >
                {employees.map((emp) => (
                  <option key={emp.id} value={emp.id}>
                    {emp.first_name} {emp.last_name}
                  </option>
                ))}
              </select>
              <input
                type="number"
                min="1"
                max="12"
                value={viewMonth}
                onChange={(e) => setViewMonth(Number(e.target.value))}
                className="w-20 rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
              <input
                type="number"
                min="2000"
                value={viewYear}
                onChange={(e) => setViewYear(Number(e.target.value))}
                className="w-24 rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
              <button
                type="button"
                onClick={loadRecords}
                disabled={recordsLoading}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
              >
                {recordsLoading ? 'Loading…' : 'Load Records'}
              </button>
            </div>

            {recordsLoading && <LoadingSpinner />}
            {!recordsLoading && recordsError && (
              <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{recordsError}</p>
            )}
            {!recordsLoading && !recordsError && records && records.records.length === 0 && (
              <EmptyState title="No attendance records" description="No records for this period." />
            )}
            {!recordsLoading && !recordsError && records && records.records.length > 0 && (
              <>
                {/* Summary */}
                <div className="mb-4 flex flex-wrap gap-3">
                  {[
                    ['Present', records.summary.total_present, 'bg-green-100 text-green-800'],
                    ['Absent', records.summary.total_absent, 'bg-red-100 text-red-800'],
                    ['Half Days', records.summary.total_half_days, 'bg-yellow-100 text-yellow-800'],
                    ['Late', records.summary.total_late_days, 'bg-orange-100 text-orange-800'],
                  ].map(([label, value, cls]) => (
                    <div key={label} className={`rounded-lg px-4 py-2 text-sm font-semibold ${cls}`}>
                      {label}: {value}
                    </div>
                  ))}
                </div>

                {/* Records table */}
                <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
                  <table className="min-w-full divide-y divide-slate-200 text-sm">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-4 py-3 text-left font-medium text-slate-600">Date</th>
                        <th className="px-4 py-3 text-left font-medium text-slate-600">Status</th>
                        <th className="px-4 py-3 text-left font-medium text-slate-600">Override By</th>
                        <th className="px-4 py-3 text-left font-medium text-slate-600">Override Reason</th>
                        <th className="px-4 py-3 text-left font-medium text-slate-600">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {records.records.map((record) => (
                        <tr key={record.id}>
                          <td className="whitespace-nowrap px-4 py-3 font-medium">{record.date}</td>
                          <td className="px-4 py-3">
                            <StatusBadge status={record.status} isOverride={record.is_override} />
                          </td>
                          <td className="px-4 py-3 font-mono text-xs text-slate-400">
                            {record.overridden_by
                              ? String(record.overridden_by).slice(0, 8) + '…'
                              : '—'}
                          </td>
                          <td className="max-w-xs truncate px-4 py-3 text-slate-500">
                            {record.override_reason || '—'}
                          </td>
                          <td className="px-4 py-3">
                            <button
                              type="button"
                              onClick={() => setOverrideRecord(record)}
                              className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                            >
                              Override
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </section>
        </div>
      )}

      {/* Override modal */}
      {overrideRecord && (
        <OverrideModal
          record={overrideRecord}
          onClose={() => setOverrideRecord(null)}
          onSuccess={handleOverrideSuccess}
        />
      )}
    </SidebarLayout>
  )
}
