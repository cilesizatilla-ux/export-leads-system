# Global Export/Import Lead Generation & Email Campaign System

Dünya çapında ihracat/ithalat yapan şirketleri bulan, ülkeye göre kategorize eden,
o ülkenin dilinde otomatik kişiselleştirilmiş email gönderen ve sonuçları takip eden
web tabanlı sistem.

## Özellikler

- 🔍 Apollo.io & Hunter.io entegrasyonu ile şirket/email/telefon bulma
- 🌍 Ülke bazlı otomatik kategorizasyon
- 🤖 Claude AI ile içerik üretimi + DeepL ile çeviri
- 📧 SendGrid ile toplu email gönderimi (PDF/sunum ekli)
- 📊 Açılma, tıklama, bounce, spam takibi (webhook)
- 🔄 A/B test ve otomatik yeniden gönderim stratejileri

## Hızlı Başlangıç

### 1. Gereksinimler
- Docker & Docker Compose
- Python 3.11+
- API anahtarları: Apollo.io, SendGrid, DeepL, Anthropic (Claude)

### 2. Kurulum

```bash
# Repoyu klonla
cd export-leads-system

# Ortam değişkenlerini ayarla
cp backend/.env.example backend/.env
# .env dosyasını düzenle ve API key'leri ekle

# Veritabanını başlat
docker-compose up -d

# Backend bağımlılıklarını yükle
cd backend
pip install -r requirements.txt

# Veritabanı tablolarını oluştur
python -m app.database

# Sunucuyu başlat
uvicorn app.main:app --reload
```

API dokümanı: http://localhost:8000/docs

## Proje Yapısı

```
backend/
├── app/
│   ├── main.py              # FastAPI giriş noktası
│   ├── database.py          # PostgreSQL bağlantısı
│   ├── core/
│   │   └── config.py        # Ayarlar (env vars)
│   ├── models/              # SQLAlchemy modelleri
│   │   ├── company.py       # Şirket
│   │   ├── contact.py       # Kişi
│   │   ├── campaign.py      # Email kampanyası
│   │   └── email_log.py     # Gönderim takibi
│   ├── schemas/             # Pydantic şemaları (request/response)
│   ├── api/                 # REST API endpoint'leri
│   │   ├── leads.py         # Şirket bulma & listeleme
│   │   ├── campaigns.py     # Kampanya yönetimi
│   │   ├── tracking.py      # Webhook & açılma takibi
│   │   └── analytics.py     # İstatistikler
│   └── services/            # İş mantığı
│       ├── apollo_service.py    # Apollo.io entegrasyonu
│       ├── hunter_service.py    # Hunter.io entegrasyonu
│       ├── translation.py       # DeepL çeviri
│       ├── ai_content.py        # Claude ile içerik üretimi
│       ├── email_sender.py      # SendGrid email gönderimi
│       └── tracker.py           # Açılma/tıklama takibi
```

## Yol Haritası

- [x] Faz 1: Altyapı + veritabanı modelleri
- [x] Faz 2: Lead generation API'leri
- [x] Faz 3: Email gönderim ve tracking
- [ ] Faz 4: Frontend (React)
- [ ] Faz 5: Gelişmiş analitik dashboard

## Yasal Uyumluluk

- ✅ GDPR uyumlu opt-out mekanizması
- ✅ CAN-SPAM Act uyumlu unsubscribe linkleri
- ✅ Sadece kamuya açık B2B verilerinin kullanımı
