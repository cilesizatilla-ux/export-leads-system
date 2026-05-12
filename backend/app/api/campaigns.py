"""
Email Kampanya Yönetimi API'si.
- Kampanya CRUD
- Kampanyayı başlatma (toplu email gönderimi)
- Çeviri ve AI içerik üretimi
"""
from datetime import datetime
from fastapi import APIRouter, Body, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.campaign import Campaign
from app.models.company import Company
from app.models.contact import Contact
from app.models.email_log import EmailLog
from app.schemas.schemas import CampaignCreate, CampaignResponse
from app.services.translation import TranslationService
from app.services.ai_content import AIContentService
from app.services.email_sender import EmailSenderService, generate_tracking_id

router = APIRouter(prefix="/api/campaigns", tags=["Campaigns"])


@router.post("", response_model=CampaignResponse)
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)):
    """Yeni kampanya oluştur (henüz göndermez, draft durumunda)."""
    campaign = Campaign(**payload.model_dump())
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.get("", response_model=list[CampaignResponse])
def list_campaigns(db: Session = Depends(get_db)):
    """Tüm kampanyaları listele."""
    return db.query(Campaign).order_by(Campaign.created_at.desc()).all()


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Kampanya bulunamadı")
    return campaign


@router.post("/{campaign_id}/translate")
def translate_campaign(
    campaign_id: int,
    target_languages: list[str] = Body(...),
    db: Session = Depends(get_db),
):
    """
    Kampanyanın subject ve body'sini hedef dillere çevir.
    Çeviriler campaign.translations alanında cache'lenir.
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Kampanya bulunamadı")

    try:
        translator = TranslationService()
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    translations = campaign.translations or {}

    for lang in target_languages:
        if lang == campaign.source_language:
            continue
        if lang in translations:
            continue  # Zaten çevrildi

        result = translator.translate_email(
            subject=campaign.subject_template,
            body_html=campaign.body_template,
            target_lang=lang,
            source_lang=campaign.source_language,
        )
        translations[lang] = {"subject": result["subject"], "body": result["body"]}

    campaign.translations = translations
    # SQLAlchemy JSON alanı için flag_modified gerekebilir
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(campaign, "translations")
    db.commit()

    return {
        "campaign_id": campaign_id,
        "translated_languages": list(translations.keys()),
    }


def _send_campaign_emails(campaign_id: int):
    """
    Background task: Kampanyayı tüm hedef contact'lara gönder.
    Burada üretim için Celery + Redis kullanılmalı; bu basit versiyon.
    """
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return

        # Hedef contact'ları seç
        query = db.query(Contact).join(Company).filter(
            Contact.is_unsubscribed == False,  # noqa
            Contact.is_bounced == False,
        )
        if campaign.target_countries:
            query = query.filter(Company.country_code.in_(campaign.target_countries))
        if campaign.target_industries:
            from sqlalchemy import or_
            query = query.filter(or_(
                *[Company.industry.ilike(f"%{ind}%") for ind in campaign.target_industries]
            ))
        if campaign.target_trade_type and campaign.target_trade_type != "both":
            query = query.filter(Company.trade_type == campaign.target_trade_type)

        contacts = query.all()

        sender = EmailSenderService()
        translator = TranslationService() if campaign.translations is not None else None
        ai = AIContentService() if campaign.use_ai_personalization else None

        campaign.status = "sending"
        campaign.started_at = datetime.utcnow()
        campaign.total_recipients = len(contacts)
        db.commit()

        sent_count = 0

        for contact in contacts:
            company = contact.company
            language = company.language or "en"

            # 1) İçeriği seç (çevrilmiş varsa onu kullan)
            translations = campaign.translations or {}
            if language in translations:
                subject = translations[language]["subject"]
                body = translations[language]["body"]
            else:
                subject = campaign.subject_template
                body = campaign.body_template

            # 2) AI ile kişiselleştir (opsiyonel)
            if ai and contact.full_name:
                try:
                    personalized = ai.generate_cold_email(
                        company_name=company.name,
                        company_industry=company.industry or "Trade",
                        company_country=company.country or "",
                        contact_name=contact.full_name,
                        contact_title=contact.title,
                        my_company_name="Your Company",  # Settings'e taşınabilir
                        my_products=campaign.body_template[:200],  # Özet olarak
                        my_value_proposition="High quality products at competitive prices",
                        tone=campaign.ai_tone,
                        language=language,
                    )
                    subject = personalized["subject"]
                    body = personalized["body"]
                except Exception as e:
                    print(f"AI personalization hata: {e}, şablon kullanılıyor")

            # 3) Tracking log oluştur
            tracking_id = generate_tracking_id()
            log = EmailLog(
                campaign_id=campaign.id,
                contact_id=contact.id,
                tracking_id=tracking_id,
                sent_subject=subject,
                sent_body=body,
                sent_language=language,
                status="queued",
            )
            db.add(log)
            db.flush()

            # 4) Email gönder
            result = sender.send_email(
                to_email=contact.email,
                to_name=contact.full_name,
                subject=subject,
                html_body=body,
                tracking_id=tracking_id,
                language=language,
                attachment_path=campaign.attachment_path,
                attachment_name=campaign.attachment_name,
                campaign_id=campaign.id,
            )

            if result["success"]:
                log.status = "sent"
                log.sent_at = datetime.utcnow()
                log.provider_message_id = result.get("message_id")
                sent_count += 1
            else:
                log.status = "failed"
                log.error_message = result.get("error")

            db.commit()

        campaign.sent_count = sent_count
        campaign.status = "completed"
        campaign.completed_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


@router.post("/{campaign_id}/start")
def start_campaign(
    campaign_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Kampanyayı arka planda gönder."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Kampanya bulunamadı")
    if campaign.status == "sending":
        raise HTTPException(status_code=400, detail="Kampanya zaten gönderiliyor")

    background_tasks.add_task(_send_campaign_emails, campaign_id)
    return {"message": "Kampanya gönderimi başlatıldı", "campaign_id": campaign_id}
