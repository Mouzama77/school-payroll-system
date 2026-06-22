import { useCallback, useEffect, useState } from 'react'

import { getAuditLogs } from '../api/audit_logs'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import SidebarLayout from '../components/SidebarLayout'

const ACTION_OPTIONS = [
  '',
  'LEAVE_APPROVED',
  'LEAVE_REJECTED',
  'ATTENDANCE_OVERRIDDEN',
]

const ENTITY_OPTIONS = ['', 'leave', 'attendance']

const PAGE_SIZE = 20

function ActionBadge({ action }) {
  const cls = {
    LEAVE_APPROVED: 'bg-green-100 text-green-800',
    LEAVE_REJECTED: 'bg-red-100 text-red-800',
    ATTENDANCE_OVERRIDDEN: 'bg-blue-100 text-blue-700',
  }
  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${cls[action] ?? 'bg-slate-100 text-slate-600'}`}
    >
      {action}
    </span>
  )
}

function formatDatetime(iso) {
  if (!iso) return '—'
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso))
}

function exportToCSV(rows) {
  const headers = ['ID', 'Actor', 'Action', 'Entity Type', 'Entity ID', 'Detail', 'Created At']
  const lines = [
    headers.join(','),
    ...rows.map((r) =>
      [
        r.id,
        r.actor_id,
        r.action,
        r.entity_type,
        r.entity_id,
        `"${(r.detail ?? '').replace(/"/g, '""')}"`,
        r.created_at,
      ].join(','),
    ),
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `audit-log-${Date.now()}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

export default function AuditLog() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)

  // Filters
  const [search, setSearch] = useState('')
  const [action, setAction] = useState('')
  const [entityType, setEntityType] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const load = useCallback(
    async (pageNum = 1, append = false) => {
      setLoading(true)
      setError('')
      try {
        const result = await getAuditLogs({
          search: search || undefined,
          action: action || undefined,
          entity_type: entityType || undefined,
          date_from: dateFrom || undefined,
          date_to: dateTo || undefined,
          page: pageNum,
          page_size: PAGE_SIZE,
        })

        // Backend may return array or { items, total } — handle both shapes
        const items = Array.isArray(result) ? result : (result.items ?? result)
        setLogs((prev) => (append ? [...prev, ...items] : items))
        setHasMore(items.length === PAGE_SIZE)
        setPage(pageNum)
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load audit logs')
      } finally {
        setLoading(false)
      }
    },
    [search, action, entityType, dateFrom, dateTo],
  )

  // Initial load and re-load when filters change
  useEffect(() => {
    load(1, false)
  }, [load])

  const handleSearch = (e) => {
    e.preventDefault()
    load(1, false)
  }

  const handleLoadMore = () => load(page + 1, true)

  const handleExport = () => {
    if (logs.length === 0) return
    exportToCSV(logs)
  }

  return (
    <SidebarLayout title="Audit Log">
      {/* Filters */}
      <form
        onSubmit={handleSearch}
        className="mb-4 flex flex-wrap items-end gap-3 rounded-xl border border-slate-200 bg-white p-4"
      >
        <div className="flex-1 min-w-48">
          <label className="mb-1 block text-xs font-medium text-slate-600">Search detail</label>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search…"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">Action</label>
          <select
            value={action}
            onChange={(e) => setAction(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            {ACTION_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>
                {opt || 'All actions'}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">Entity</label>
          <select
            value={entityType}
            onChange={(e) => setEntityType(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            {ENTITY_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>
                {opt || 'All entities'}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">From</label>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">To</label>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <button
          type="submit"
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white"
        >
          Filter
        </button>
        <button
          type="button"
          disabled={logs.length === 0}
          onClick={handleExport}
          className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
        >
          Export CSV
        </button>
      </form>

      {/* States */}
      {loading && page === 1 && <LoadingSpinner />}
      {!loading && error && (
        <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>
      )}
      {!loading && !error && logs.length === 0 && (
        <EmptyState title="No audit logs" description="No events match the current filters." />
      )}

      {/* Table */}
      {logs.length > 0 && (
        <>
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Time</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Action</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Entity</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Entity ID</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Actor</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Detail</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td className="whitespace-nowrap px-4 py-3 text-xs text-slate-500">
                      {formatDatetime(log.created_at)}
                    </td>
                    <td className="px-4 py-3">
                      <ActionBadge action={log.action} />
                    </td>
                    <td className="px-4 py-3 text-slate-600">{log.entity_type}</td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-400">
                      {String(log.entity_id).slice(0, 8)}…
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-400">
                      {String(log.actor_id).slice(0, 8)}…
                    </td>
                    <td className="max-w-sm truncate px-4 py-3 text-slate-500">
                      {log.detail || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Load more */}
          {hasMore && (
            <div className="mt-4 flex justify-center">
              <button
                type="button"
                disabled={loading}
                onClick={handleLoadMore}
                className="rounded-lg border border-slate-300 px-5 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60"
              >
                {loading ? 'Loading…' : 'Load more'}
              </button>
            </div>
          )}
        </>
      )}
    </SidebarLayout>
  )
}
