"""
EmailLog modeli: Her gönderilen emailin tam takibi.
Spam/bounce/açılma/tıklama olaylarını tutar.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship

from app.database import Base


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)

    # İlişkiler
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), index=True)

    # Tracking ID - URL'lerde kullanılır (UUID benzeri)
    tracking_id = Column(String(64), unique=True, index=True, nullable=False)

    # Gönderilen içerik (kişiselleştirilmiş ve çevrilmiş)
    sent_subject = Column(String(500))
    sent_body = Column(Text)
    sent_language = Column(String(10))

    # SendGrid mesaj ID (webhook'lar için)
    provider_message_id = Column(String(255), index=True)

    # Takip ayrıntıları
    follow_up_number = Column(Integer, default=0)     # 0 = ilk email, 1 = ilk takip vb.

    # Durum (en güncel)
    status = Column(String(50), default="queued", index=True)
    # "queued", "sent", "delivered", "opened", "clicked",
    # "bounced", "spam", "blocked", "replied", "unsubscribed", "failed"

    # Olay zaman damgaları
    queued_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    first_opened_at = Column(DateTime)
    last_opened_at = Column(DateTime)
    first_clicked_at = Column(DateTime)
    last_clicked_at = Column(DateTime)
    bounced_at = Column(DateTime)
    spam_at = Column(DateTime)
    replied_at = Column(DateTime)

    # Sayaçlar
    open_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)

    # Hata bilgisi
    error_message = Column(Text)
    bounce_reason = Column(String(255))

    # Tüm olayların tam geçmişi (debug için)
    events = Column(JSON, default=list)
    # [{"type": "delivered", "timestamp": "...", "raw": {...}}, ...]

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    campaign = relationship("Campaign", back_populates="email_logs")
    contact = relationship("Contact", back_populates="email_logs")

    __table_args__ = (
        Index("idx_emaillog_campaign_status", "campaign_id", "status"),
        Index("idx_emaillog_contact_status", "contact_id", "status"),
    )

    def __repr__(self):
        return f"<EmailLog {self.tracking_id} [{self.status}]>"
