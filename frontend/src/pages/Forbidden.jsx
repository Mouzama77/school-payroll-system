import { Link } from 'react-router-dom'

import SidebarLayout from '../components/SidebarLayout'

export default function Forbidden() {
  return (
    <SidebarLayout title="Access denied">
      <div className="max-w-xl rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-red-600">403</p>
        <h2 className="mt-2 text-2xl font-semibold text-slate-900">
          You do not have access to this page.
        </h2>
        <p className="mt-3 text-sm text-slate-600">
          Your account role does not include permission for this area.
        </p>
        <Link
          to="/dashboard"
          className="mt-6 inline-block rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white"
        >
          Back to dashboard
        </Link>
      </div>
    </SidebarLayout>
  )
}
