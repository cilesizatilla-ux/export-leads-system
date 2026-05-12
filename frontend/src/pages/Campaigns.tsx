import { useEffect, useState } from 'react'
import { getCampaigns, createCampaign, startCampaign } from '../api'
import type { Campaign } from '../api'
import { Link } from 'react-router-dom'

const statusColor: Record<string, string> = {
  draft: 'bg-slate-100 text-slate-600',
  sending: 'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
  scheduled: 'bg-yellow-100 text-yellow-700',
  paused: 'bg-orange-100 text-orange-700',
}

const EMPTY_FORM = {
  name: '', description: '', subject_template: '', body_template: '',
  source_language: 'en', target_countries: '', target_industries: '',
  send_rate_per_hour: 50, use_ai_personalization: true, ai_tone: 'professional',
}

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const load = () => getCampaigns().then(setCampaigns).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const handleCreate = async () => {
    if (!form.name || !form.subject_template || !form.body_template) {
      setError('Name, subject and body are required.'); return
    }
    setSaving(true); setError('')
    try {
      const body = {
        ...form,
        target_countries: form.target_countries ? form.target_countries.split(',').map(s => s.trim().toUpperCase()) : null,
        target_industries: form.target_industries ? form.target_industries.split(',').map(s => s.trim()) : null,
      }
      await createCampaign(body)
      setShowForm(false)
      setForm(EMPTY_FORM)
      load()
    } catch (e: any) { setError(e.message) }
    setSaving(false)
  }

  const handleStart = async (id: number) => {
    if (!confirm('Start sending this campaign?')) return
    try {
      await startCampaign(id)
      load()
    } catch (e: any) { alert(e.message) }
  }

  if (loading) return <p className="text-slate-400">Loading…</p>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Campaigns</h1>
        <button onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors">
          + New Campaign
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-4">
          <h2 className="font-semibold text-slate-800">New Campaign</h2>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <div className="grid grid-cols-2 gap-4">
            {[
              { label: 'Campaign Name *', key: 'name', placeholder: 'Q3 Germany Outreach' },
              { label: 'Description', key: 'description', placeholder: 'Optional description' },
              { label: 'Target Countries (comma-sep)', key: 'target_countries', placeholder: 'DE, AT, CH' },
              { label: 'Target Industries (comma-sep)', key: 'target_industries', placeholder: 'Manufacturing, Logistics' },
            ].map(({ label, key, placeholder }) => (
              <div key={key}>
                <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
                <input value={(form as any)[key]} onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                  placeholder={placeholder}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400" />
              </div>
            ))}
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Subject Line *</label>
            <input value={form.subject_template} onChange={e => setForm(f => ({ ...f, subject_template: e.target.value }))}
              placeholder="Premium products from Turkey"
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Email Body (HTML) *</label>
            <textarea value={form.body_template} onChange={e => setForm(f => ({ ...f, body_template: e.target.value }))}
              rows={5} placeholder="<p>Dear {{name}},</p><p>We would like to introduce...</p>"
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 font-mono" />
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Source Language</label>
              <select value={form.source_language} onChange={e => setForm(f => ({ ...f, source_language: e.target.value }))}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400">
                {['en', 'tr', 'de', 'fr', 'es'].map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">AI Tone</label>
              <select value={form.ai_tone} onChange={e => setForm(f => ({ ...f, ai_tone: e.target.value }))}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400">
                {['professional', 'friendly', 'formal'].map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Send Rate (per hour)</label>
              <input type="number" value={form.send_rate_per_hour}
                onChange={e => setForm(f => ({ ...f, send_rate_per_hour: Number(e.target.value) }))}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400" />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" id="ai" checked={form.use_ai_personalization}
              onChange={e => setForm(f => ({ ...f, use_ai_personalization: e.target.checked }))}
              className="rounded" />
            <label htmlFor="ai" className="text-sm text-slate-700">Use Claude AI personalization</label>
          </div>
          <div className="flex gap-3 pt-2">
            <button onClick={handleCreate} disabled={saving}
              className="px-5 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors">
              {saving ? 'Creating…' : 'Create Campaign'}
            </button>
            <button onClick={() => { setShowForm(false); setError('') }}
              className="px-5 py-2 bg-slate-100 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-200 transition-colors">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* List */}
      <div className="bg-white rounded-xl border border-slate-200">
        {campaigns.length === 0 ? (
          <p className="px-6 py-8 text-slate-400 text-sm">No campaigns yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="text-left text-slate-500 border-b border-slate-100 bg-slate-50">
              <tr>
                {['Name', 'Status', 'Recipients', 'Sent', 'Opened', 'Created', 'Actions'].map(h => (
                  <th key={h} className="px-4 py-3 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {campaigns.map(c => (
                <tr key={c.id} className="border-t border-slate-50 hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-slate-800">
                    <Link to={`/campaigns/${c.id}`} className="hover:text-indigo-600">{c.name}</Link>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColor[c.status] || 'bg-slate-100 text-slate-600'}`}>
                      {c.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{c.total_recipients}</td>
                  <td className="px-4 py-3 text-slate-600">{c.sent_count}</td>
                  <td className="px-4 py-3 text-slate-600">{c.opened_count}</td>
                  <td className="px-4 py-3 text-slate-400">{new Date(c.created_at).toLocaleDateString()}</td>
                  <td className="px-4 py-3 flex gap-2">
                    <Link to={`/campaigns/${c.id}`}
                      className="px-3 py-1 text-xs bg-slate-100 text-slate-700 rounded hover:bg-slate-200 transition-colors">
                      Details
                    </Link>
                    {c.status === 'draft' && (
                      <button onClick={() => handleStart(c.id)}
                        className="px-3 py-1 text-xs bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors">
                        Start
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
