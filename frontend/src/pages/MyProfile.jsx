import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { getEmployees } from '../api/employees'
import LoadingSpinner from '../components/LoadingSpinner'
import SidebarLayout from '../components/SidebarLayout'
import { useToast } from '../context/ToastContext'
import { formatCurrency } from '../utils/auth'

export default function MyProfile() {
  const { showToast } = useToast()
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getEmployees()
      .then((data) => setProfile(data[0]))
      .catch((err) => showToast(err.response?.data?.detail || 'Failed to load profile', 'error'))
      .finally(() => setLoading(false))
  }, [showToast])

  return (
    <SidebarLayout title="My Profile">
      {loading && <LoadingSpinner />}
      {!loading && profile && (
        <div className="max-w-2xl rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold">
            {profile.first_name} {profile.last_name}
          </h2>
          <dl className="mt-6 space-y-3 text-sm">
            <div className="flex justify-between border-b border-slate-100 pb-2">
              <dt className="text-slate-500">Email</dt>
              <dd className="font-medium">{profile.email}</dd>
            </div>
            <div className="flex justify-between border-b border-slate-100 pb-2">
              <dt className="text-slate-500">Salary</dt>
              <dd className="font-medium">{formatCurrency(profile.salary)}</dd>
            </div>
            <div className="flex justify-between border-b border-slate-100 pb-2">
              <dt className="text-slate-500">Joining Date</dt>
              <dd className="font-medium">{profile.joining_date}</dd>
            </div>
            <div className="flex justify-between border-b border-slate-100 pb-2">
              <dt className="text-slate-500">Status</dt>
              <dd className="font-medium">{profile.status || 'active'}</dd>
            </div>
          </dl>
          <Link
            to="/change-password"
            className="mt-6 inline-block rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white"
          >
            Change Password
          </Link>
        </div>
      )}
    </SidebarLayout>
  )
}
