# Feature: Global Email Discovery

**Role requesting:** Project Director (Atilla)
**Team executing:** Software Analyst, Backend Expert, Database Expert, Frontend Expert, Testing Expert

---

## Requirement

> "Bring email addresses from companies from different countries all over the world."

---

## Software Analyst — Specification

### Problem
PDL (People Data Labs) free tier: 500 credits exhausted. No company discovery possible.

### Solution
Two-stage pipeline, both stages free:

1. **Stage 1 — Company Discovery: Wikidata SPARQL**
   - Source: `https://query.wikidata.org/sparql`
   - No API key required. No rate limit on normal usage.
   - Returns registered businesses by country + optional keyword filter on company name
   - Coverage: 200+ countries via Wikidata QID mapping
   - Returns: company name + website URL

2. **Stage 2 — Email Discovery: Hunter.io**
   - Already integrated (25 free searches/month on free plan)
   - Takes each domain from Stage 1
   - Returns: first name, last name, email, title, department

### Data Flow
```
User selects: Countries + Industry/Keywords
      ↓
Wikidata SPARQL → list of (name, domain, country_code)
      ↓  [per domain]
Hunter.io domain_search → list of (email, name, title)
      ↓
PostgreSQL → companies + contacts tables
```

### Constraints
- Wikidata covers only notable companies (those with Wikipedia entries)
- Hunter free: 25 domain searches/month — upgrade for scale
- PDL endpoint (`/search/apollo`) remains available for when credits are topped up

---

## Backend Expert — Implementation

### New file
`backend/app/services/clearbit_service.py` — contains `WikidataService` (aliased as `ClearbitService` for backward compatibility)

### New endpoint
`POST /api/leads/search/global`

**Request body:** same `LeadSearchRequest` schema as PDL endpoint
```json
{
  "countries": ["DE", "FR", "GB"],
  "industries": ["manufacturing"],
  "keywords": ["logistics", "importer"],
  "per_page": 50,
  "save_to_db": true
}
```

**Response:** same `LeadSearchResponse` schema
```json
{
  "total_found": 32,
  "saved_count": 32,
  "companies": [...]
}
```

### Key logic
- One SPARQL query per country (parallel not needed — queries are fast ~1.5s each)
- `limit_per_country = per_page` (default 25)
- Keyword filter applied in SPARQL `FILTER(CONTAINS(LCASE(?name), "..."))` 
- Deduplication by domain across countries
- Hunter called per domain, errors silently logged

---

## Database Expert — Schema Impact

No schema changes required. Companies saved with `source = "wikidata"`. Existing indexes on `domain`, `country_code`, and composite `(country_code, industry)` handle queries efficiently.

---

## Frontend Expert — UI Changes

`frontend/src/pages/Leads.tsx`:
- Added third tab: **"🌍 Global Search (Free)"** — default active tab
- Shared country pill selector + industry/keyword inputs across Global and PDL tabs
- Results table: clickable domain links open company website

`frontend/src/api.ts`:
- Added `searchGlobal(body)` → `POST /api/leads/search/global`

---

## Testing Expert — Test Cases

| Test | Expected |
|---|---|
| Search DE + "manufacturing" | Returns German manufacturing companies with `.de` domains |
| Search FR + "logistics" | Returns French logistics companies with `country_code: FR` |
| Search multiple countries | Companies deduplicated by domain across countries |
| Unknown country code | Skipped with log message, no crash |
| No keywords | Returns all businesses for that country |
| Hunter unavailable | Companies still saved, contacts skipped gracefully |
| save_to_db=false | Returns preview companies without DB write |

---

## Limitations & Next Steps

| Limitation | Mitigation |
|---|---|
| Wikidata = notable companies only | Good for B2B outreach (established firms) |
| No industry filter in Wikidata (only name keyword filter) | Use descriptive keywords: "pharma", "textile", "logistics" |
| Hunter 25/month on free plan | Upgrade Hunter ($49/mo = 500 searches) |
| PDL still preferred for precision | Top up PDL credits when needed |

---

*Implemented: 2026-05-12 | Team: Full Team*
