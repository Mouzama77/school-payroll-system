import { useEffect, useState } from 'react'

import {
  createAcademicCalendarEntry,
  getAcademicCalendarEntries,
} from '../api/academic_calendar'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import SidebarLayout from '../components/SidebarLayout'
import { useToast } from '../context/ToastContext'

const DAY_TYPES = [
  'WORKING_DAY',
  'SCHOOL_HOLIDAY',
  'EXAM_HOLIDAY',
  'VACATION',
]

export default function AcademicCalendar() {
  const { showToast } = useToast()
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [dayType, setDayType] = useState(DAY_TYPES[0])
  const [description, setDescription] = useState('')

  const loadEntries = async () => {
    setLoading(true)
    try {
      setEntries(await getAcademicCalendarEntries())
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to load academic calendar', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadEntries()
  }, [])

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!date) return showToast('Select a date', 'error')
    if (!dayType) return showToast('Select a day type', 'error')

    setSubmitting(true)
    try {
      await createAcademicCalendarEntry({
        date,
        day_type: dayType,
        description: description || null,
      })
      showToast('Academic calendar entry created')
      setDescription('')
      setDayType(DAY_TYPES[0])
      loadEntries()
    } catch (err) {
      showToast(err.response?.data?.detail || 'Create failed', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <SidebarLayout title="Academic Calendar">
      <form
        onSubmit={handleSubmit}
        className="mb-6 max-w-2xl rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
      >
        <div className="grid gap-4 sm:grid-cols-3">
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
            <label className="mb-1 block text-xs font-medium text-slate-700">Day Type</label>
            <select
              required
              value={dayType}
              onChange={(e) => setDayType(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            >
              {DAY_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-slate-700">Description</label>
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
        </div>

        <div className="mt-4">
          <button
            type="submit"
            disabled={submitting}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
          >
            {submitting ? 'Submitting…' : 'Add Calendar Entry'}
          </button>
        </div>
      </form>

      {loading && <LoadingSpinner />}

      {!loading && entries.length === 0 && <EmptyState title="No academic calendar entries" />}

      {!loading && entries.length > 0 && (
        <div className="grid gap-4">
          {entries.map((entry) => (
            <div key={entry.id} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-slate-900">{entry.date}</p>
                  <p className="mt-1 text-xs uppercase tracking-wide text-slate-500">{entry.day_type}</p>
                </div>
                <p className="text-sm text-slate-500">{entry.description || '—'}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </SidebarLayout>
  )
}
