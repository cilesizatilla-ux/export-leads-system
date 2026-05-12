"""
Analytics API'si: Kampanya performans raporları.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.database import get_db
from app.models.campaign import Campaign
from app.models.email_log import EmailLog
from app.models.contact import Contact
from app.models.company import Company
from app.schemas.schemas import CampaignAnalytics

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/campaigns/{campaign_id}", response_model=CampaignAnalytics)
def campaign_analytics(campaign_id: int, db: Session = Depends(get_db)):
    """Bir kampanyanın detaylı analitiği."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Kampanya bulunamadı")

    # Status sayıları
    status_counts = dict(
        db.query(EmailLog.status, func.count(EmailLog.id))
        .filter(EmailLog.campaign_id == campaign_id)
        .group_by(EmailLog.status)
        .all()
    )

    sent = sum(v for k, v in status_counts.items() if k != "queued" and k != "failed")
    delivered = status_counts.get("delivered", 0) + status_counts.get("opened", 0) + status_counts.get("clicked", 0) + status_counts.get("replied", 0)
    opened = status_counts.get("opened", 0) + status_counts.get("clicked", 0) + status_counts.get("replied", 0)
    clicked = status_counts.get("clicked", 0) + status_counts.get("replied", 0)
    bounced = status_counts.get("bounced", 0)
    spam = status_counts.get("spam", 0)
    replied = status_counts.get("replied", 0)
    unsubscribed = status_counts.get("unsubscribed", 0)

    # Ülke bazlı kırılım
    country_stats = (
        db.query(
            Company.country_code,
            func.count(EmailLog.id).label("total"),
            func.sum(case((EmailLog.first_opened_at.isnot(None), 1), else_=0)).label("opened"),
            func.sum(case((EmailLog.first_clicked_at.isnot(None), 1), else_=0)).label("clicked"),
        )
        .join(Contact, EmailLog.contact_id == Contact.id)
        .join(Company, Contact.company_id == Company.id)
        .filter(EmailLog.campaign_id == campaign_id)
        .group_by(Company.country_code)
        .all()
    )

    by_country = {
        row[0] or "Unknown": {
            "sent": row[1],
            "opened": int(row[2] or 0),
            "clicked": int(row[3] or 0),
        }
        for row in country_stats
    }

    return CampaignAnalytics(
        campaign_id=campaign.id,
        campaign_name=campaign.name,
        total_recipients=campaign.total_recipients or 0,
        sent=sent,
        delivered=delivered,
        opened=opened,
        clicked=clicked,
        bounced=bounced,
        spam=spam,
        replied=replied,
        unsubscribed=unsubscribed,
        open_rate=round(opened / sent * 100, 2) if sent else 0,
        click_rate=round(clicked / sent * 100, 2) if sent else 0,
        bounce_rate=round(bounced / sent * 100, 2) if sent else 0,
        by_country=by_country,
    )


@router.get("/dashboard")
def dashboard_summary(db: Session = Depends(get_db)):
    """Genel dashboard istatistikleri."""
    return {
        "totals": {
            "companies": db.query(Company).count(),
            "contacts": db.query(Contact).count(),
            "campaigns": db.query(Campaign).count(),
            "emails_sent": db.query(EmailLog).filter(EmailLog.sent_at.isnot(None)).count(),
        },
        "active_campaigns": db.query(Campaign).filter(
            Campaign.status.in_(["sending", "scheduled"])
        ).count(),
        "recent_campaigns": [
            {
                "id": c.id,
                "name": c.name,
                "status": c.status,
                "sent": c.sent_count,
                "opened": c.opened_count,
            }
            for c in db.query(Campaign).order_by(Campaign.created_at.desc()).limit(5).all()
        ],
    }


@router.get("/campaigns/{campaign_id}/logs")
def campaign_logs(
    campaign_id: int,
    status: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Bir kampanyanın email loglarını listele."""
    query = db.query(EmailLog).filter(EmailLog.campaign_id == campaign_id)
    if status:
        query = query.filter(EmailLog.status == status)
    return query.offset(skip).limit(limit).all()
