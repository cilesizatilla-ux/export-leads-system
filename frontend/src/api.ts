const BASE = '/api'

async function request<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// Leads
export const searchLeads = (body: object) =>
  request('/leads/search/apollo', { method: 'POST', body: JSON.stringify(body) })

export const searchGlobal = (body: object) =>
  request('/leads/search/global', { method: 'POST', body: JSON.stringify(body) })

export const searchHunter = (domain: string, limit = 10) =>
  request(`/leads/search/hunter?domain=${domain}&limit=${limit}`, { method: 'POST' })

export const getCompanies = (params?: Record<string, string>) => {
  const q = params ? '?' + new URLSearchParams(params).toString() : ''
  return request<Company[]>('/leads/companies' + q)
}

export const getContacts = (params?: Record<string, string>) => {
  const q = params ? '?' + new URLSearchParams(params).toString() : ''
  return request<Contact[]>('/leads/contacts' + q)
}

export const getLeadStats = () => request<LeadStats>('/leads/stats')

// Campaigns
export const getCampaigns = () => request<Campaign[]>('/campaigns')
export const getCampaign = (id: number) => request<Campaign>(`/campaigns/${id}`)
export const createCampaign = (body: object) =>
  request<Campaign>('/campaigns', { method: 'POST', body: JSON.stringify(body) })
export const startCampaign = (id: number) =>
  request(`/campaigns/${id}/start`, { method: 'POST' })

// Analytics
export const getDashboard = () => request<Dashboard>('/analytics/dashboard')
export const getCampaignAnalytics = (id: number) =>
  request<CampaignAnalytics>(`/analytics/campaigns/${id}`)

// Types
export interface Company {
  id: number; name: string; domain: string | null; website: string | null
  country: string | null; country_code: string | null; language: string | null
  industry: string | null; trade_type: string | null; phone: string | null
  created_at: string
}
export interface Contact {
  id: number; company_id: number; first_name: string | null; last_name: string | null
  full_name: string | null; title: string | null; email: string
  is_unsubscribed: boolean; is_bounced: boolean; created_at: string
}
export interface LeadStats {
  total_companies: number; total_contacts: number; active_contacts: number
  country_distribution: { country_code: string; count: number }[]
}
export interface Campaign {
  id: number; name: string; status: string; total_recipients: number
  sent_count: number; opened_count: number; clicked_count: number
  bounced_count: number; replied_count: number; created_at: string
}
export interface Dashboard {
  totals: { companies: number; contacts: number; campaigns: number; emails_sent: number }
  active_campaigns: number
  recent_campaigns: { id: number; name: string; status: string; sent: number; opened: number }[]
}
export interface CampaignAnalytics {
  campaign_id: number; campaign_name: string; total_recipients: number
  sent: number; delivered: number; opened: number; clicked: number
  bounced: number; spam: number; replied: number; unsubscribed: number
  open_rate: number; click_rate: number; bounce_rate: number
  by_country: Record<string, { sent: number; opened: number; clicked: number }>
}
