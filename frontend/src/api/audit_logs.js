import { api } from './axios'

/**
 * Fetch paginated audit log entries.
 *
 * @param {object} params
 * @param {string}  [params.search]      - Free-text search against detail field
 * @param {string}  [params.action]      - Filter by action label (e.g. LEAVE_APPROVED)
 * @param {string}  [params.entity_type] - Filter by entity type (e.g. leave, attendance)
 * @param {string}  [params.date_from]   - ISO date string (inclusive)
 * @param {string}  [params.date_to]     - ISO date string (inclusive)
 * @param {number}  [params.page=1]
 * @param {number}  [params.page_size=20]
 */
export async function getAuditLogs(params = {}) {
  const { data } = await api.get('/audit-logs/', { params })
  return data
}
