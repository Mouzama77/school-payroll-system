import { useEffect, useState } from 'react'

import { adminResetPassword, createUser, deleteUser, getUsers } from '../api/users'
import ConfirmDialog from '../components/ConfirmDialog'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import SidebarLayout from '../components/SidebarLayout'
import { useToast } from '../context/ToastContext'

export default function Users() {
  const { showToast } = useToast()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({ email: '', password: '', role: 'employee' })
  const [deleteTarget, setDeleteTarget] = useState(null)

  const loadUsers = async () => {
    setLoading(true)
    try {
      setUsers(await getUsers())
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to load users', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadUsers()
  }, [])

  const handleCreate = async (event) => {
    event.preventDefault()
    try {
      await createUser({ ...form, must_change_password: true })
      showToast('User created')
      setForm({ email: '', password: '', role: 'employee' })
      loadUsers()
    } catch (err) {
      showToast(err.response?.data?.detail || 'Create failed', 'error')
    }
  }

  const handleResetPassword = async (userId) => {
    try {
      await adminResetPassword(userId, {
        new_password: 'Temp@2026!',
        must_change_password: true,
      })
      showToast('Password reset to Temp@2026!')
    } catch (err) {
      showToast(err.response?.data?.detail || 'Reset failed', 'error')
    }
  }

  const handleDelete = async () => {
    try {
      await deleteUser(deleteTarget.id)
      showToast('User deleted')
      setDeleteTarget(null)
      loadUsers()
    } catch (err) {
      showToast(err.response?.data?.detail || 'Delete failed', 'error')
    }
  }

  return (
    <SidebarLayout title="Users">
      <form onSubmit={handleCreate} className="mb-6 grid gap-3 rounded-xl border border-slate-200 bg-white p-5 shadow-sm md:grid-cols-4">
        <input
          type="email"
          required
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          placeholder="Email"
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
        <input
          type="password"
          required
          minLength={8}
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          placeholder="Password"
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
        <select
          value={form.role}
          onChange={(e) => setForm({ ...form, role: e.target.value })}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="employee">Employee</option>
          <option value="hr">HR</option>
          <option value="admin">Admin</option>
        </select>
        <button type="submit" className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white">
          Create User
        </button>
      </form>

      {loading && <LoadingSpinner />}
      {!loading && users.length === 0 && <EmptyState title="No users found" />}
      {!loading && users.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left">Email</th>
                <th className="px-4 py-3 text-left">Role</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {users.map((user) => (
                <tr key={user.id}>
                  <td className="px-4 py-3">{user.email}</td>
                  <td className="px-4 py-3 capitalize">{user.role}</td>
                  <td className="px-4 py-3">{user.is_active ? 'Active' : 'Inactive'}</td>
                  <td className="px-4 py-3 space-x-2">
                    <button
                      type="button"
                      onClick={() => handleResetPassword(user.id)}
                      className="text-blue-600 hover:underline"
                    >
                      Reset password
                    </button>
                    <button
                      type="button"
                      onClick={() => setDeleteTarget(user)}
                      className="text-red-600 hover:underline"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete user"
        message={`Delete ${deleteTarget?.email}? This cannot be undone.`}
        confirmLabel="Delete"
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </SidebarLayout>
  )
}
