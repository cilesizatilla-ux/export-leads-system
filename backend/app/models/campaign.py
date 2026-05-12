"""
Campaign modeli: Email kampanyaları.
Bir kampanya = belirli bir hedef kitleye gönderilen email serisi.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)

    # Kampanya bilgileri
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Hedefleme
    target_countries = Column(JSON)                   # ["DE", "FR", "ES"]
    target_industries = Column(JSON)                  # ["Manufacturing", "Logistics"]
    target_trade_type = Column(String(50))            # "exporter", "importer", "both"

    # Email içeriği (orijinal - kaynak dil)
    source_language = Column(String(10), default="en")
    subject_template = Column(String(500), nullable=False)
    body_template = Column(Text, nullable=False)      # HTML
    body_text = Column(Text)                           # Plain text alternatifi

    # Çevrilmiş içerikler (ülke diline göre cache)
    # {"de": {"subject": "...", "body": "..."}, "fr": {...}}
    translations = Column(JSON, default=dict)

    # Eklenecek dosya (PDF/sunum)
    attachment_path = Column(String(500))             # Yerel dosya yolu
    attachment_name = Column(String(255))

    # Strateji ayarları
    send_rate_per_hour = Column(Integer, default=50)  # Saatte kaç email
    follow_up_days = Column(Integer, default=7)       # Takip emaili kaç gün sonra
    max_follow_ups = Column(Integer, default=3)       # En fazla kaç takip

    # Durum
    status = Column(String(50), default="draft", index=True)
    # "draft", "scheduled", "sending", "paused", "completed"

    # Tarihler
    scheduled_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Sonuçlar (performans için cache)
    total_recipients = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    bounced_count = Column(Integer, default=0)
    replied_count = Column(Integer, default=0)
    unsubscribed_count = Column(Integer, default=0)

    # AI ayarları
    use_ai_personalization = Column(Boolean, default=True)
    ai_tone = Column(String(50), default="professional")  # professional, friendly, formal

    # İlişkiler
    email_logs = relationship("EmailLog", back_populates="campaign", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Campaign {self.name} [{self.status}]>"
