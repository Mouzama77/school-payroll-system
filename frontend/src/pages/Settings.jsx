import { Link } from 'react-router-dom'

import SidebarLayout from '../components/SidebarLayout'

export default function Settings() {
  return (
    <SidebarLayout title="Settings">
      <div className="max-w-2xl space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <h2 className="font-semibold text-slate-900">Account Security</h2>
          <p className="mt-1 text-sm text-slate-500">
            Manage your password and account preferences.
          </p>
          <Link
            to="/change-password"
            className="mt-3 inline-block rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white"
          >
            Change Password
          </Link>
        </div>
        <div className="border-t border-slate-200 pt-4">
          <h2 className="font-semibold text-slate-900">System</h2>
          <p className="mt-1 text-sm text-slate-500">
            Configure environment variables and deployment settings via backend `.env`.
          </p>
        </div>
      </div>
    </SidebarLayout>
  )
}
