import { useEffect, useState } from 'react'
import { getCompanies, getContacts, getLeadStats } from '../api'
import type { Company, Contact, LeadStats } from '../api'

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([])
  const [contacts, setContacts] = useState<Contact[]>([])
  const [stats, setStats] = useState<LeadStats | null>(null)
  const [tab, setTab] = useState<'companies' | 'contacts'>('companies')
  const [filterCountry, setFilterCountry] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getCompanies(),
      getContacts(),
      getLeadStats(),
    ]).then(([c, ct, s]) => {
      setCompanies(c)
      setContacts(ct)
      setStats(s)
      setLoading(false)
    })
  }, [])

  const filteredCompanies = filterCountry
    ? companies.filter(c => c.country_code === filterCountry)
    : companies

  const countryCodes = [...new Set(companies.map(c => c.country_code).filter(Boolean))] as string[]

  if (loading) return <p className="text-slate-400">Loading…</p>

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Companies & Contacts</h1>
          <p className="text-slate-500 text-sm mt-1">
            {stats?.total_companies} companies · {stats?.active_contacts} active contacts
          </p>
        </div>
        {/* Country distribution */}
        {stats && stats.country_distribution.length > 0 && (
          <div className="flex gap-2 flex-wrap justify-end">
            {stats.country_distribution.slice(0, 6).map(({ country_code, count }) => (
              <span key={country_code} className="px-2 py-1 bg-slate-100 rounded-lg text-xs text-slate-600">
                <span className="font-mono font-bold">{country_code || '??'}</span> {count}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        {(['companies', 'contacts'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${tab === t ? 'bg-indigo-600 text-white' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'}`}>
            {t === 'companies' ? `Companies (${companies.length})` : `Contacts (${contacts.length})`}
          </button>
        ))}
      </div>

      {tab === 'companies' && (
        <div className="bg-white rounded-xl border border-slate-200">
          {/* Filter */}
          <div className="px-6 py-3 border-b border-slate-100 flex gap-2 flex-wrap">
            <button onClick={() => setFilterCountry('')}
              className={`px-3 py-1 rounded-full text-xs font-medium border ${!filterCountry ? 'bg-indigo-600 text-white border-indigo-600' : 'border-slate-200 text-slate-600 hover:border-indigo-300'}`}>
              All
            </button>
            {countryCodes.map(code => (
              <button key={code} onClick={() => setFilterCountry(code)}
                className={`px-3 py-1 rounded-full text-xs font-medium border ${filterCountry === code ? 'bg-indigo-600 text-white border-indigo-600' : 'border-slate-200 text-slate-600 hover:border-indigo-300'}`}>
                {code}
              </button>
            ))}
          </div>
          {filteredCompanies.length === 0 ? (
            <p className="px-6 py-8 text-slate-400 text-sm">No companies yet. Use Lead Search to find some.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-slate-500 border-b border-slate-100 bg-slate-50">
                  <tr>
                    {['Company', 'Domain', 'Country', 'Industry', 'Language', 'Added'].map(h => (
                      <th key={h} className="px-4 py-3 font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredCompanies.map(c => (
                    <tr key={c.id} className="border-t border-slate-50 hover:bg-slate-50">
                      <td className="px-4 py-3 font-medium text-slate-800">{c.name}</td>
                      <td className="px-4 py-3 text-slate-500">
                        {c.domain ? (
                          <a href={`https://${c.domain}`} target="_blank" rel="noreferrer"
                            className="text-indigo-600 hover:underline">{c.domain}</a>
                        ) : '—'}
                      </td>
                      <td className="px-4 py-3">
                        {c.country_code && (
                          <span className="px-2 py-0.5 bg-slate-100 rounded text-xs font-mono">{c.country_code}</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-slate-500">{c.industry || '—'}</td>
                      <td className="px-4 py-3 text-slate-500">{c.language || '—'}</td>
                      <td className="px-4 py-3 text-slate-400">{new Date(c.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === 'contacts' && (
        <div className="bg-white rounded-xl border border-slate-200">
          {contacts.length === 0 ? (
            <p className="px-6 py-8 text-slate-400 text-sm">No contacts yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-slate-500 border-b border-slate-100 bg-slate-50">
                  <tr>
                    {['Name', 'Email', 'Title', 'Status', 'Added'].map(h => (
                      <th key={h} className="px-4 py-3 font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {contacts.map(c => (
                    <tr key={c.id} className="border-t border-slate-50 hover:bg-slate-50">
                      <td className="px-4 py-3 font-medium text-slate-800">{c.full_name || '—'}</td>
                      <td className="px-4 py-3 font-mono text-indigo-600">{c.email}</td>
                      <td className="px-4 py-3 text-slate-500">{c.title || '—'}</td>
                      <td className="px-4 py-3">
                        {c.is_bounced
                          ? <span className="px-2 py-0.5 bg-red-100 text-red-600 rounded-full text-xs">Bounced</span>
                          : c.is_unsubscribed
                          ? <span className="px-2 py-0.5 bg-orange-100 text-orange-600 rounded-full text-xs">Unsub</span>
                          : <span className="px-2 py-0.5 bg-green-100 text-green-600 rounded-full text-xs">Active</span>
                        }
                      </td>
                      <td className="px-4 py-3 text-slate-400">{new Date(c.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
