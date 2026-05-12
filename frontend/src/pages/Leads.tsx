import { useState } from 'react'
import { searchLeads, searchGlobal, searchHunter } from '../api'

const COUNTRIES = [
  { code: 'DE', name: 'Germany' }, { code: 'FR', name: 'France' },
  { code: 'GB', name: 'United Kingdom' }, { code: 'IT', name: 'Italy' },
  { code: 'ES', name: 'Spain' }, { code: 'NL', name: 'Netherlands' },
  { code: 'PL', name: 'Poland' }, { code: 'TR', name: 'Turkey' },
  { code: 'US', name: 'United States' }, { code: 'CN', name: 'China' },
  { code: 'JP', name: 'Japan' }, { code: 'BR', name: 'Brazil' },
  { code: 'IN', name: 'India' }, { code: 'AU', name: 'Australia' },
  { code: 'CA', name: 'Canada' }, { code: 'AE', name: 'UAE' },
  { code: 'SA', name: 'Saudi Arabia' }, { code: 'RU', name: 'Russia' },
]

interface SearchResult {
  total_found: number
  saved_count: number
  companies: { id: number; name: string; domain: string | null; country: string | null; country_code: string | null; industry: string | null; language: string | null }[]
}

export default function LeadsPage() {
  const [tab, setTab] = useState<'global' | 'pdl' | 'hunter'>('global')

  // Shared search state
  const [countries, setCountries] = useState<string[]>([])
  const [industry, setIndustry] = useState('')
  const [keywords, setKeywords] = useState('')
  const [perPage, setPerPage] = useState(10)
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null)

  // Hunter form
  const [domain, setDomain] = useState('')
  const [hunterResult, setHunterResult] = useState<any>(null)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const toggleCountry = (code: string) =>
    setCountries(prev => prev.includes(code) ? prev.filter(c => c !== code) : [...prev, code])

  const buildBody = (extra: Record<string, unknown> = {}) => {
    const body: Record<string, unknown> = { save_to_db: true, ...extra }
    if (countries.length) body.countries = countries
    if (industry) body.industries = [industry]
    if (keywords) body.keywords = keywords.split(',').map(k => k.trim()).filter(Boolean)
    return body
  }

  const runGlobal = async () => {
    setLoading(true); setError(''); setSearchResult(null)
    try {
      const res = await searchGlobal(buildBody()) as SearchResult
      setSearchResult(res)
    } catch (e: any) { setError(e.message) }
    setLoading(false)
  }

  const runPDL = async () => {
    setLoading(true); setError(''); setSearchResult(null)
    try {
      const res = await searchLeads(buildBody({ per_page: perPage })) as SearchResult
      setSearchResult(res)
    } catch (e: any) { setError(e.message) }
    setLoading(false)
  }

  const runHunter = async () => {
    if (!domain) return
    setLoading(true); setError(''); setHunterResult(null)
    try {
      const res = await searchHunter(domain)
      setHunterResult(res)
    } catch (e: any) { setError(e.message) }
    setLoading(false)
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">Lead Search</h1>

      {/* Tabs */}
      <div className="flex gap-2">
        {(['global', 'pdl', 'hunter'] as const).map(t => (
          <button key={t} onClick={() => { setTab(t); setSearchResult(null); setError('') }}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${tab === t ? 'bg-indigo-600 text-white' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'}`}>
            {t === 'global' ? '🌍 Global Search (Free)' : t === 'pdl' ? 'PDL Search' : 'Find Emails (Hunter)'}
          </button>
        ))}
      </div>

      {/* Shared search form for Global and PDL tabs */}
      {(tab === 'global' || tab === 'pdl') && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-slate-800">
                {tab === 'global' ? 'Global Company Search — Wikidata' : 'People Data Labs — Company Search'}
              </h2>
              {tab === 'global' && (
                <p className="text-xs text-green-600 mt-0.5">
                  Free · No API credits · Searches across all countries automatically
                </p>
              )}
            </div>
          </div>

          {/* Countries */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Countries</label>
            <div className="flex flex-wrap gap-2">
              {COUNTRIES.map(({ code, name }) => (
                <button key={code} onClick={() => toggleCountry(code)}
                  className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${countries.includes(code) ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white text-slate-600 border-slate-200 hover:border-indigo-300'}`}>
                  {name}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Industry</label>
              <input value={industry} onChange={e => setIndustry(e.target.value)}
                placeholder="e.g. manufacturing, logistics"
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Keywords (comma-separated)</label>
              <input value={keywords} onChange={e => setKeywords(e.target.value)}
                placeholder="e.g. textile, export, importer"
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400" />
            </div>
          </div>

          <div className="flex items-center gap-4">
            {tab === 'pdl' && (
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Results per page</label>
                <select value={perPage} onChange={e => setPerPage(Number(e.target.value))}
                  className="border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400">
                  {[5, 10, 25, 50].map(n => <option key={n} value={n}>{n}</option>)}
                </select>
              </div>
            )}
            <button onClick={tab === 'global' ? runGlobal : runPDL} disabled={loading}
              className={`${tab === 'pdl' ? 'mt-5' : ''} px-5 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors`}>
              {loading ? 'Searching…' : tab === 'global' ? '🌍 Search Globally' : 'Search'}
            </button>
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          {searchResult && (
            <div>
              <p className="text-sm text-slate-500 mb-3">
                Found <strong>{searchResult.total_found}</strong> companies — <strong>{searchResult.saved_count}</strong> saved to database
              </p>
              <div className="overflow-x-auto rounded-lg border border-slate-100">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50 text-slate-500">
                    <tr>
                      {['Company', 'Domain', 'Country', 'Industry', 'Language'].map(h => (
                        <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {searchResult.companies.map(c => (
                      <tr key={c.id} className="border-t border-slate-100 hover:bg-slate-50">
                        <td className="px-4 py-3 font-medium text-slate-800">{c.name}</td>
                        <td className="px-4 py-3 text-slate-500">
                          {c.domain
                            ? <a href={`https://${c.domain}`} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">{c.domain}</a>
                            : '—'}
                        </td>
                        <td className="px-4 py-3">
                          {c.country_code && (
                            <span className="px-2 py-0.5 bg-slate-100 rounded text-xs font-mono">{c.country_code}</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-slate-500">{c.industry || '—'}</td>
                        <td className="px-4 py-3 text-slate-500">{c.language || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'hunter' && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-5">
          <h2 className="font-semibold text-slate-800">Hunter.io — Find Emails by Domain</h2>
          <div className="flex gap-3">
            <input value={domain} onChange={e => setDomain(e.target.value)}
              placeholder="e.g. siemens.com"
              className="flex-1 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              onKeyDown={e => e.key === 'Enter' && runHunter()} />
            <button onClick={runHunter} disabled={loading || !domain}
              className="px-5 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors">
              {loading ? 'Searching…' : 'Find Emails'}
            </button>
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          {hunterResult && (
            <div>
              <p className="text-sm text-slate-500 mb-3">
                <strong>{hunterResult.company?.name}</strong> — {hunterResult.contacts_count} contacts found
              </p>
              <div className="overflow-x-auto rounded-lg border border-slate-100">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50 text-slate-500">
                    <tr>
                      {['Email', 'Name', 'Title'].map(h => (
                        <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {hunterResult.contacts?.map((c: any) => (
                      <tr key={c.email} className="border-t border-slate-100 hover:bg-slate-50">
                        <td className="px-4 py-3 font-mono text-indigo-600">{c.email}</td>
                        <td className="px-4 py-3 text-slate-700">{c.name || '—'}</td>
                        <td className="px-4 py-3 text-slate-500">{c.title || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
