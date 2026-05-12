"""
Export/Import Lead Generation & Email Campaign System
Ana FastAPI uygulaması.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.api import leads, campaigns, tracking, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başlangıcında DB tablolarını oluştur."""
    print("🚀 Uygulama başlatılıyor...")
    try:
        init_db()
    except Exception as e:
        print(f"⚠️ DB init uyarısı: {e}")
    yield
    print("👋 Uygulama kapatılıyor...")


app = FastAPI(
    title="Global Export/Import Leads System",
    description="Şirket bul, ülkeye göre kategorize et, dilinde email gönder, takip et.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - Frontend'in API'ye erişebilmesi için
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Üretimde sadece kendi domain'ini ekle
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ları bağla
app.include_router(leads.router)
app.include_router(campaigns.router)
app.include_router(tracking.router)
app.include_router(analytics.router)


@app.get("/")
def root():
    return {
        "name": "Global Export/Import Leads System",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "leads": "/api/leads",
            "campaigns": "/api/campaigns",
            "tracking": "/api/tracking",
            "analytics": "/api/analytics",
        },
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
