"""
Pydantic şemaları: API'ye gelen ve giden veri yapılarını tanımlar.
SQLAlchemy modellerinin "transport katmanı".
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ============= Company =============
class CompanyBase(BaseModel):
    name: str
    domain: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = Field(None, max_length=2)
    language: Optional[str] = None
    industry: Optional[str] = None
    trade_type: Optional[str] = None  # exporter, importer, both
    products: Optional[str] = None
    phone: Optional[str] = None
    general_email: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyResponse(CompanyBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ============= Contact =============
class ContactBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    title: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None


class ContactCreate(ContactBase):
    company_id: int


class ContactResponse(ContactBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    is_unsubscribed: bool
    is_bounced: bool
    created_at: datetime


# ============= Lead Search =============
class LeadSearchRequest(BaseModel):
    """Apollo veya Hunter ile lead arama isteği."""
    keywords: Optional[list[str]] = None
    countries: Optional[list[str]] = Field(
        None, description="ISO ülke kodları, örn: ['DE', 'FR']"
    )
    industries: Optional[list[str]] = None
    titles: Optional[list[str]] = Field(
        None, description="Hedef pozisyonlar, örn: ['Purchasing Manager']"
    )
    employee_ranges: Optional[list[str]] = None
    page: int = 1
    per_page: int = 25
    save_to_db: bool = Field(True, description="Bulunanları DB'ye kaydet")


class LeadSearchResponse(BaseModel):
    total_found: int
    saved_count: int
    companies: list[CompanyResponse]


# ============= Campaign =============
class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    target_countries: Optional[list[str]] = None
    target_industries: Optional[list[str]] = None
    target_trade_type: Optional[str] = None
    source_language: str = "en"
    subject_template: str
    body_template: str  # HTML
    body_text: Optional[str] = None
    attachment_path: Optional[str] = None
    attachment_name: Optional[str] = None
    send_rate_per_hour: int = 50
    follow_up_days: int = 7
    max_follow_ups: int = 3
    use_ai_personalization: bool = True
    ai_tone: str = "professional"


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    status: str
    total_recipients: int
    sent_count: int
    opened_count: int
    clicked_count: int
    bounced_count: int
    replied_count: int
    created_at: datetime


class CampaignStartRequest(BaseModel):
    """Kampanyayı başlatma: hangi contact'lara gönderilecek."""
    contact_ids: Optional[list[int]] = Field(
        None, description="None ise hedefleme kriterlerine uyan tüm contact'lar"
    )
    test_mode: bool = Field(False, description="True ise sadece ilk 3 kişiye gönder")


# ============= Email Log =============
class EmailLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tracking_id: str
    campaign_id: int
    contact_id: int
    status: str
    sent_at: Optional[datetime]
    first_opened_at: Optional[datetime]
    open_count: int
    click_count: int
    error_message: Optional[str]


# ============= Analytics =============
class CampaignAnalytics(BaseModel):
    campaign_id: int
    campaign_name: str
    total_recipients: int
    sent: int
    delivered: int
    opened: int
    clicked: int
    bounced: int
    spam: int
    replied: int
    unsubscribed: int
    open_rate: float
    click_rate: float
    bounce_rate: float
    by_country: dict  # {"DE": {"sent": 10, "opened": 5}}
