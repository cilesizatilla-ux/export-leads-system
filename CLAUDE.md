# Export/Import Lead Generation & Email Campaign System

B2B lead generation tool that finds international companies via PDL, discovers their contacts via Hunter.io, and sends multi-language cold email campaigns tracked via SendGrid.

## Stack
- **Backend:** Python 3.9, FastAPI, SQLAlchemy 2.0, PostgreSQL
- **Services:** PDL (companies), Hunter.io (emails), SendGrid (sending), Claude claude-sonnet-4-6 (AI personalization), DeepL (translation)

## Running Locally
```bash
# Start PostgreSQL (first time only)
brew services start postgresql@16

# Start server
cd backend
PYTHONPATH=. python3 -m uvicorn app.main:app --port 8000 --reload
```

## Key Files
| File | Purpose |
|---|---|
| `backend/app/api/leads.py` | PDL company search + Hunter email lookup |
| `backend/app/api/campaigns.py` | Campaign CRUD + background email sending |
| `backend/app/api/analytics.py` | Campaign performance reports |
| `backend/app/api/tracking.py` | Open/click pixel + SendGrid webhook |
| `backend/app/services/pdl_service.py` | People Data Labs API (replaces Apollo) |
| `backend/app/services/hunter_service.py` | Hunter.io email finder |
| `backend/app/services/email_sender.py` | SendGrid sender with tracking injection |
| `backend/app/services/ai_content.py` | Claude AI cold email generator |
| `backend/app/services/translation.py` | DeepL HTML-aware translation |
| `backend/app/core/config.py` | All settings loaded from `.env` |

## API Keys (.env)
- `PDL_API_KEY` — peopledatalabs.com (account: atilla@keyofsustain.com)
- `HUNTER_API_KEY` — hunter.io
- `SENDGRID_API_KEY` — sendgrid.com
- `ANTHROPIC_API_KEY` — anthropic.com
- `DEEPL_API_KEY` — deepl.com (not yet set)

## Lead Search Flow
1. `POST /api/leads/search/apollo` → PDL finds companies by country/industry
2. Per company with a domain → Hunter.io finds emails automatically
3. Companies + contacts saved to PostgreSQL

## Pending
- GitHub remote: run `gh auth login` then push
- DeepL key: add to `.env` to enable campaign translation
