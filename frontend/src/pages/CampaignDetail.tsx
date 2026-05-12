import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getCampaign, getCampaignAnalytics, startCampaign } from '../api'
import type { Campaign, CampaignAnalytics } from '../api'

const Stat = ({ label, value, sub }: { label: string; value: number | string; sub?: string }) => (
  <div className="bg-white rounded-xl border border-slate-200 p-5">
    <p className="text-sm text-slate-500">{label}</p>
    <p className="text-2xl font-bold text-slate-900 mt-1">{value}</p>
    {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
  </div>
)

export default function CampaignDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [campaign, setCampaign] = useState<Campaign | null>(null)
  const [analytics, setAnalytics] = useState<CampaignAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState(false)

  useEffect(() => {
    const n = Number(id)
    Promise.all([getCampaign(n), getCampaignAnalytics(n).catch(() => null)])
      .then(([c, a]) => { setCampaign(c); setAnalytics(a) })
      .finally(() => setLoading(false))
  }, [id])

  const handleStart = async () => {
    if (!confirm('Start sending this campaign?')) return
    setStarting(true)
    try {
      await startCampaign(Number(id))
      const c = await getCampaign(Number(id))
      setCampaign(c)
    } catch (e: any) { alert(e.message) }
    setStarting(false)
  }

  if (loading) return <p className="text-slate-400">Loading…</p>
  if (!campaign) return <p className="text-red-500">Campaign not found.</p>

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link to="/campaigns" className="text-sm text-slate-400 hover:text-slate-600">← Campaigns</Link>
          <h1 className="text-2xl font-bold text-slate-900 mt-1">{campaign.name}</h1>
          <span className={`inline-block mt-1 px-2 py-0.5 rounded-full text-xs font-medium ${
            campaign.status === 'completed' ? 'bg-green-100 text-green-700' :
            campaign.status === 'sending' ? 'bg-blue-100 text-blue-700' :
            'bg-slate-100 text-slate-600'
          }`}>{campaign.status}</span>
        </div>
        {campaign.status === 'draft' && (
          <button onClick={handleStart} disabled={starting}
            className="px-5 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors">
            {starting ? 'Starting…' : '▶ Start Campaign'}
          </button>
        )}
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat label="Recipients" value={campaign.total_recipients} />
        <Stat label="Sent" value={campaign.sent_count} />
        <Stat label="Opened" value={campaign.opened_count}
          sub={analytics ? `${analytics.open_rate}% open rate` : undefined} />
        <Stat label="Clicked" value={campaign.clicked_count}
          sub={analytics ? `${analytics.click_rate}% click rate` : undefined} />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat label="Bounced" value={campaign.bounced_count}
          sub={analytics ? `${analytics.bounce_rate}% bounce rate` : undefined} />
        <Stat label="Replied" value={campaign.replied_count} />
        <Stat label="Delivered" value={analytics?.delivered ?? '—'} />
        <Stat label="Unsubscribed" value={analytics?.unsubscribed ?? '—'} />
      </div>

      {/* Country breakdown */}
      {analytics && Object.keys(analytics.by_country).length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="font-semibold text-slate-800">By Country</h2>
          </div>
          <table className="w-full text-sm">
            <thead className="text-left text-slate-500 border-b border-slate-100 bg-slate-50">
              <tr>
                {['Country', 'Sent', 'Opened', 'Clicked'].map(h => (
                  <th key={h} className="px-6 py-3 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Object.entries(analytics.by_country).map(([country, data]) => (
                <tr key={country} className="border-t border-slate-50 hover:bg-slate-50">
                  <td className="px-6 py-3">
                    <span className="font-mono font-bold text-slate-700">{country}</span>
                  </td>
                  <td className="px-6 py-3 text-slate-600">{data.sent}</td>
                  <td className="px-6 py-3 text-slate-600">{data.opened}</td>
                  <td className="px-6 py-3 text-slate-600">{data.clicked}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
