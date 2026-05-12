"""
Company modeli: İhracat/ithalat yapan şirket bilgileri.
Apollo, Hunter veya manuel olarak eklenir.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Index
from sqlalchemy.orm import relationship

from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)

    # Temel bilgiler
    name = Column(String(255), nullable=False, index=True)
    domain = Column(String(255), unique=True, index=True)
    website = Column(String(500))

    # Lokasyon (ülke bazlı kategorizasyon için kritik)
    country = Column(String(100), index=True)        # Örn: "Germany"
    country_code = Column(String(2), index=True)     # ISO: "DE"
    language = Column(String(10), index=True)        # Örn: "de", "en", "tr"
    city = Column(String(255))
    address = Column(Text)

    # İş bilgileri
    industry = Column(String(255), index=True)
    sub_industry = Column(String(255))
    employee_count = Column(String(50))               # Örn: "50-200"
    annual_revenue = Column(String(100))
    founded_year = Column(Integer)

    # İhracat/İthalat tipi
    trade_type = Column(String(50), index=True)       # "exporter", "importer", "both"
    products = Column(Text)                            # Ürün/hizmet açıklaması

    # İletişim
    phone = Column(String(50))
    general_email = Column(String(255))

    # Kaynak takibi
    source = Column(String(50))                        # "apollo", "hunter", "manual"
    source_id = Column(String(255))                    # Kaynak sistemdeki ID
    raw_data = Column(JSON)                            # Kaynaktan gelen ham veri

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    contacts = relationship("Contact", back_populates="company", cascade="all, delete-orphan")

    # Aramayı hızlandırmak için bileşik indeks
    __table_args__ = (
        Index("idx_company_country_industry", "country_code", "industry"),
    )

    def __repr__(self):
        return f"<Company {self.name} ({self.country_code})>"
