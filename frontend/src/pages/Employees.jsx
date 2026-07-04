import { useEffect, useState } from 'react'

import { getDepartments } from '../api/departments'
import { getDesignations } from '../api/designations'
import {
  createEmployee,
  deleteEmployee,
  getEmployees,
  updateEmployee,
} from '../api/employees'
import ConfirmDialog from '../components/ConfirmDialog'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import SidebarLayout from '../components/SidebarLayout'
import { useToast } from '../context/ToastContext'
import { formatCurrency } from '../utils/auth'

// Roles are static; no backend /roles endpoint exists
const ROLE_OPTIONS = [
  { value: '11111111-1111-1111-1111-111111111111', label: 'Admin' },
  { value: '22222222-2222-2222-2222-222222222222', label: 'Employee' },
  { value: '33333333-3333-3333-3333-333333333333', label: 'HR' },
]

const EMPTY_FORM = {
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  salary: '',
  joining_date: '',
  department_id: '',
  role_id: '',
  designation_id: '',
}

function EmployeeModal({ title, initial, departments, designations, onSubmit, onClose, loading }) {
  const [form, setForm] = useState(initial || EMPTY_FORM)

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = (e) => {
    e.preventDefault()
    const payload = {
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      email: form.email.trim(),
      phone: form.phone.trim() || null,
      salary: parseFloat(form.salary),
      joining_date: form.joining_date,
      department_id: form.department_id,
      role_id: form.role_id,
      designation_id: form.designation_id || null,
    }
    onSubmit(payload)
  }

  const inputCls = 'rounded-lg border border-slate-300 px-3 py-2 text-sm w-full'
  const labelCls = 'block text-xs font-medium text-slate-700 mb-1'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4">
      <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl overflow-y-auto max-h-[90vh]">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">{title}</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelCls}>First name *</label>
              <input required className={inputCls} value={form.first_name} onChange={set('first_name')} />
            </div>
            <div>
              <label className={labelCls}>Last name *</label>
              <input required className={inputCls} value={form.last_name} onChange={set('last_name')} />
            </div>
          </div>

          <div>
            <label className={labelCls}>Email *</label>
            <input required type="email" className={inputCls} value={form.email} onChange={set('email')} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelCls}>Phone</label>
              <input className={inputCls} value={form.phone} onChange={set('phone')} placeholder="Optional" />
            </div>
            <div>
              <label className={labelCls}>Salary *</label>
              <input required type="number" min="0" step="0.01" className={inputCls} value={form.salary} onChange={set('salary')} />
            </div>
          </div>

          <div>
            <label className={labelCls}>Joining date *</label>
            <input required type="date" className={inputCls} value={form.joining_date} onChange={set('joining_date')} />
          </div>

          <div>
            <label className={labelCls}>Department *</label>
            <select required className={inputCls} value={form.department_id} onChange={set('department_id')}>
              <option value="">— select department —</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className={labelCls}>Role *</label>
            <select required className={inputCls} value={form.role_id} onChange={set('role_id')}>
              <option value="">— select role —</option>
              {ROLE_OPTIONS.map((r) => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className={labelCls}>Designation</label>
            <select className={inputCls} value={form.designation_id} onChange={set('designation_id')}>
              <option value="">— none —</option>
              {designations.map((d) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>

          <div className="flex justify-end gap-3 pt-2">
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
              {loading ? 'Saving…' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function Employees() {
  const { showToast } = useToast()
  const [employees, setEmployees] = useState([])
  const [departments, setDepartments] = useState([])
  const [designations, setDesignations] = useState([])
  const [loading, setLoading] = useState(true)
  const [modalMode, setModalMode] = useState(null) // 'create' | 'edit'
  const [editTarget, setEditTarget] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [saving, setSaving] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const [emps, depts, desigs] = await Promise.all([
        getEmployees(),
        getDepartments(),
        getDesignations(),
      ])
      setEmployees(emps)
      setDepartments(depts)
      setDesignations(desigs)
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to load data', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleCreate = async (payload) => {
    setSaving(true)
    try {
      await createEmployee(payload)
      showToast('Employee created')
      setModalMode(null)
      load()
    } catch (err) {
      showToast(err.response?.data?.detail || 'Create failed', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleEdit = async (payload) => {
    setSaving(true)
    try {
      await updateEmployee(editTarget.id, payload)
      showToast('Employee updated')
      setModalMode(null)
      setEditTarget(null)
      load()
    } catch (err) {
      showToast(err.response?.data?.detail || 'Update failed', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    try {
      await deleteEmployee(deleteTarget.id)
      showToast('Employee deleted')
      setDeleteTarget(null)
      load()
    } catch (err) {
      showToast(err.response?.data?.detail || 'Delete failed', 'error')
    }
  }

  const openEdit = (emp) => {
    setEditTarget(emp)
    setModalMode('edit')
  }

  // Build initial form values for edit (map from EmployeeResponse shape)
  const editInitial = editTarget
    ? {
        first_name: editTarget.first_name,
        last_name: editTarget.last_name,
        email: editTarget.email,
        phone: editTarget.phone || '',
        salary: String(editTarget.salary),
        joining_date: editTarget.joining_date,
        department_id: editTarget.department_id,
        role_id: editTarget.role_id,
        designation_id: editTarget.designation_id || '',
      }
    : EMPTY_FORM

  return (
    <SidebarLayout title="Employees">
      <div className="mb-4 flex justify-end">
        <button
          type="button"
          onClick={() => setModalMode('create')}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white"
        >
          + Add Employee
        </button>
      </div>

      {loading && <LoadingSpinner />}

      {!loading && employees.length === 0 && (
        <EmptyState title="No employees" description="Add employees to get started." />
      )}

      {!loading && employees.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Name</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Email</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Salary</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Status</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {employees.map((emp) => (
                <tr key={emp.id}>
                  <td className="px-4 py-3 font-medium">
                    {emp.first_name} {emp.last_name}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{emp.email}</td>
                  <td className="px-4 py-3 text-slate-600">{formatCurrency(emp.salary)}</td>
                  <td className="px-4 py-3">
                    <span className="rounded-full bg-green-50 px-2 py-1 text-xs font-medium text-green-700">
                      {emp.status || 'active'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-3">
                      <button
                        type="button"
                        onClick={() => openEdit(emp)}
                        className="text-sm text-blue-600 hover:underline"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => setDeleteTarget(emp)}
                        className="text-sm text-red-600 hover:underline"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {modalMode === 'create' && (
        <EmployeeModal
          title="Add Employee"
          initial={EMPTY_FORM}
          departments={departments}
          designations={designations}
          onSubmit={handleCreate}
          onClose={() => setModalMode(null)}
          loading={saving}
        />
      )}

      {modalMode === 'edit' && editTarget && (
        <EmployeeModal
          title="Edit Employee"
          initial={editInitial}
          departments={departments}
          designations={designations}
          onSubmit={handleEdit}
          onClose={() => { setModalMode(null); setEditTarget(null) }}
          loading={saving}
        />
      )}

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete employee"
        message={`Delete ${deleteTarget?.first_name} ${deleteTarget?.last_name}?`}
        confirmLabel="Delete"
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </SidebarLayout>
  )
}
