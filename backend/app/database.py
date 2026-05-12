"""
PostgreSQL veritabanı bağlantısı ve SQLAlchemy session yönetimi.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Bağlantı kopukluğunu otomatik tespit et
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Session:
    """FastAPI dependency: Her istekte yeni bir DB session aç ve sonra kapat."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Tüm tabloları oluştur. İlk kurulumda çalıştırılır."""
    # Modelleri import etmek tabloların metadata'ya kaydolmasını sağlar
    from app.models import company, contact, campaign, email_log  # noqa: F401
    Base.metadata.create_all(bind=engine)
    print("✅ Veritabanı tabloları oluşturuldu.")


if __name__ == "__main__":
    init_db()
