"""
Contact modeli: Şirketlerdeki ilgili kişiler (CEO, satınalma müdürü vb.).
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)

    # Kişisel bilgiler
    first_name = Column(String(100))
    last_name = Column(String(100))
    full_name = Column(String(255), index=True)

    # Pozisyon
    title = Column(String(255))                       # "CEO", "Purchasing Manager"
    department = Column(String(100))
    seniority = Column(String(50))                    # "C-level", "Director", "Manager"

    # İletişim
    email = Column(String(255), unique=True, index=True, nullable=False)
    email_verified = Column(Boolean, default=False)
    email_status = Column(String(50))                 # "valid", "risky", "invalid"
    phone = Column(String(50))
    mobile = Column(String(50))
    linkedin_url = Column(String(500))

    # Email kampanya durumu
    is_unsubscribed = Column(Boolean, default=False, index=True)
    unsubscribed_at = Column(DateTime)
    bounce_count = Column(Integer, default=0)
    is_bounced = Column(Boolean, default=False, index=True)

    # Metadata
    source = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    company = relationship("Company", back_populates="contacts")
    email_logs = relationship("EmailLog", back_populates="contact", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_contact_active", "is_unsubscribed", "is_bounced"),
    )

    def __repr__(self):
        return f"<Contact {self.full_name} <{self.email}>>"
