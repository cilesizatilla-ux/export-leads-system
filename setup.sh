#!/bin/bash
# Hızlı kurulum scripti
# Kullanım: bash setup.sh

set -e  # Hata olursa dur

echo "🚀 Export Leads System - Kurulum başlıyor..."
echo ""

# 1) .env dosyası kontrolü
if [ ! -f "backend/.env" ]; then
    echo "📝 .env dosyası oluşturuluyor..."
    cp backend/.env.example backend/.env
    echo "⚠️  ÖNEMLİ: backend/.env dosyasını açıp API anahtarlarını ekleyin!"
    echo "   - APOLLO_API_KEY"
    echo "   - HUNTER_API_KEY"
    echo "   - SENDGRID_API_KEY"
    echo "   - DEEPL_API_KEY"
    echo "   - ANTHROPIC_API_KEY"
    echo ""
fi

# 2) Docker servislerini başlat
echo "🐳 PostgreSQL ve Redis başlatılıyor..."
docker-compose up -d
echo "⏳ Veritabanı hazır olana kadar bekleniyor..."
sleep 5

# 3) Python bağımlılıkları
echo "📦 Python paketleri yükleniyor..."
cd backend
pip install -r requirements.txt

# 4) DB tabloları
echo "🗄️  Veritabanı tabloları oluşturuluyor..."
python -m app.database

# 5) Server'ı başlat
echo ""
echo "✅ Kurulum tamamlandı!"
echo ""
echo "Sunucuyu başlatmak için:"
echo "    cd backend && uvicorn app.main:app --reload"
echo ""
echo "API Dokümanı: http://localhost:8000/docs"
