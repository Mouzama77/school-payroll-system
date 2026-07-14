import { useEffect, useState } from 'react'

import { createDesignation, getDesignations } from '../api/designations'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import SidebarLayout from '../components/SidebarLayout'
import { useToast } from '../context/ToastContext'

export default function Designations() {
  const { showToast } = useToast()
  const [designations, setDesignations] = useState([])
  const [loading, setLoading] = useState(true)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const data = await getDesignations()
      setDesignations(data)
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to load designations', 'error')
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
      await createDesignation({ name, description: description || null })
      showToast('Designation created')
      setName('')
      setDescription('')
      load()
    } catch (err) {
      showToast(err.response?.data?.detail || 'Create failed', 'error')
    }
  }

  return (
    <SidebarLayout title="Designations">
      <form
        onSubmit={handleCreate}
        className="mb-6 grid gap-3 rounded-xl border border-slate-200 bg-white p-5 shadow-sm md:grid-cols-3"
      >
        <input
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Designation name"
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
        <input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description (optional)"
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
        <button
          type="submit"
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white"
        >
          Add Designation
        </button>
      </form>

      {loading && <LoadingSpinner />}
      {!loading && designations.length === 0 && <EmptyState title="No designations" />}
      {!loading && designations.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          {designations.map((desig) => (
            <div
              key={desig.id}
              className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
            >
              <h3 className="font-semibold text-slate-900">{desig.name}</h3>
              <p className="mt-1 text-sm text-slate-500">{desig.description || '—'}</p>
            </div>
          ))}
        </div>
      )}
    </SidebarLayout>
  )
}
