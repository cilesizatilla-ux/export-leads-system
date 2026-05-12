import { useEffect, useState } from 'react'
import { getDashboard } from '../api'
import type { Dashboard } from '../api'
import { Link } from 'react-router-dom'

const statusColor: Record<string, string> = {
  draft: 'bg-slate-100 text-slate-600',
  sending: 'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
  scheduled: 'bg-yellow-100 text-yellow-700',
  paused: 'bg-orange-100 text-orange-700',
}

export default function DashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getDashboard().then(setData).catch(e => setError(e.message))
  }, [])

  if (error) return <p className="text-red-500">{error}</p>
  if (!data) return <p className="text-slate-400">Loading…</p>

  const cards = [
    { label: 'Companies', value: data.totals.companies, to: '/companies' },
    { label: 'Contacts', value: data.totals.contacts, to: '/companies' },
    { label: 'Campaigns', value: data.totals.campaigns, to: '/campaigns' },
    { label: 'Emails Sent', value: data.totals.emails_sent, to: '/campaigns' },
  ]

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-500 text-sm mt-1">
          {data.active_campaigns} active campaign{data.active_campaigns !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map(({ label, value, to }) => (
          <Link
            key={label}
            to={to}
            className="bg-white rounded-xl border border-slate-200 p-5 hover:shadow-md transition-shadow"
          >
            <p className="text-sm text-slate-500">{label}</p>
            <p className="text-3xl font-bold text-slate-900 mt-1">{value.toLocaleString()}</p>
          </Link>
        ))}
      </div>

      {/* Recent campaigns */}
      <div className="bg-white rounded-xl border border-slate-200">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="font-semibold text-slate-800">Recent Campaigns</h2>
          <Link to="/campaigns" className="text-indigo-600 text-sm hover:underline">View all →</Link>
        </div>
        {data.recent_campaigns.length === 0 ? (
          <p className="px-6 py-8 text-slate-400 text-sm">No campaigns yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-100">
                <th className="px-6 py-3 font-medium">Name</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium">Sent</th>
                <th className="px-6 py-3 font-medium">Opened</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_campaigns.map(c => (
                <tr key={c.id} className="border-b border-slate-50 hover:bg-slate-50">
                  <td className="px-6 py-3">
                    <Link to={`/campaigns/${c.id}`} className="font-medium text-slate-800 hover:text-indigo-600">
                      {c.name}
                    </Link>
                  </td>
                  <td className="px-6 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColor[c.status] || 'bg-slate-100 text-slate-600'}`}>
                      {c.status}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-slate-600">{c.sent}</td>
                  <td className="px-6 py-3 text-slate-600">{c.opened}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
