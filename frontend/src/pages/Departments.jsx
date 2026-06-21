import { useEffect, useState } from 'react'

import {
  createDepartment,
  deleteDepartment,
  getDepartments,
  updateDepartment,
} from '../api/departments'
import ConfirmDialog from '../components/ConfirmDialog'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import SidebarLayout from '../components/SidebarLayout'
import { useToast } from '../context/ToastContext'

export default function Departments() {
  const { showToast } = useToast()
  const [departments, setDepartments] = useState([])
  const [loading, setLoading] = useState(true)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [deleteTarget, setDeleteTarget] = useState(null)

  const load = async () => {
    setLoading(true)
    try {
      setDepartments(await getDepartments())
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to load departments', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const handleCreate = async (event) => {
    event.preventDefault()
    try {
      await createDepartment({ name, description })
      showToast('Department created')
      setName('')
      setDescription('')
      load()
    } catch (err) {
      showToast(err.response?.data?.detail || 'Create failed', 'error')
    }
  }

  const handleDelete = async () => {
    try {
      await deleteDepartment(deleteTarget.id)
      showToast('Department deleted')
      setDeleteTarget(null)
      load()
    } catch (err) {
      showToast(err.response?.data?.detail || 'Delete failed', 'error')
    }
  }

  return (
    <SidebarLayout title="Departments">
      <form onSubmit={handleCreate} className="mb-6 grid gap-3 rounded-xl border border-slate-200 bg-white p-5 shadow-sm md:grid-cols-3">
        <input
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Department name"
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
        <input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description"
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
        <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white">
          Add Department
        </button>
      </form>

      {loading && <LoadingSpinner />}
      {!loading && departments.length === 0 && <EmptyState title="No departments" />}
      {!loading && departments.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          {departments.map((department) => (
            <div key={department.id} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-slate-900">{department.name}</h3>
                  <p className="mt-1 text-sm text-slate-500">{department.description || '—'}</p>
                </div>
                <button
                  type="button"
                  onClick={() => setDeleteTarget(department)}
                  className="text-sm text-red-600 hover:underline"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete department"
        message={`Delete ${deleteTarget?.name}?`}
        confirmLabel="Delete"
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </SidebarLayout>
  )
}
