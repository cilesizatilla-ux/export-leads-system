"""
Email Tracking API'si.
- Açılma takibi (pixel image endpoint)
- Tıklama takibi (link redirect)
- SendGrid webhook (delivered, bounced, spam, vb.)
- Unsubscribe endpoint
"""
import base64
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.database import get_db
from app.models.email_log import EmailLog
from app.models.contact import Contact
from app.models.campaign import Campaign

router = APIRouter(prefix="/api/tracking", tags=["Tracking"])


# 1x1 transparent GIF (base64 encoded)
TRACKING_PIXEL = base64.b64decode(
    "R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=="
)


@router.get("/pixel/{tracking_id}.gif")
def track_open(tracking_id: str, request: Request, db: Session = Depends(get_db)):
    """
    Email açıldığında bu endpoint çağrılır (görünmez pixel).
    Tarayıcı/email client image'i indirir.
    """
    log = db.query(EmailLog).filter(EmailLog.tracking_id == tracking_id).first()
    if log:
        now = datetime.utcnow()
        log.open_count = (log.open_count or 0) + 1
        log.last_opened_at = now
        if not log.first_opened_at:
            log.first_opened_at = now
            # İlk açılış: status'ı güncelle
            if log.status in ("sent", "delivered"):
                log.status = "opened"
            # Kampanya sayacını artır
            campaign = db.query(Campaign).filter(Campaign.id == log.campaign_id).first()
            if campaign:
                campaign.opened_count = (campaign.opened_count or 0) + 1

        # Event geçmişi
        events = log.events or []
        events.append({
            "type": "open",
            "timestamp": now.isoformat(),
            "user_agent": request.headers.get("user-agent"),
            "ip": request.client.host if request.client else None,
        })
        log.events = events
        flag_modified(log, "events")
        db.commit()

    # Pixel'i her zaman döndür (bulunmasa bile)
    return Response(content=TRACKING_PIXEL, media_type="image/gif")


@router.get("/click/{tracking_id}")
def track_click(tracking_id: str, url: str, db: Session = Depends(get_db)):
    """
    Email içindeki linkler bu endpoint'e yönlendirilir.
    Tıklama kaydedilir, sonra gerçek URL'ye redirect.
    """
    log = db.query(EmailLog).filter(EmailLog.tracking_id == tracking_id).first()
    if log:
        now = datetime.utcnow()
        log.click_count = (log.click_count or 0) + 1
        log.last_clicked_at = now
        if not log.first_clicked_at:
            log.first_clicked_at = now
            log.status = "clicked"
            campaign = db.query(Campaign).filter(Campaign.id == log.campaign_id).first()
            if campaign:
                campaign.clicked_count = (campaign.clicked_count or 0) + 1

        events = log.events or []
        events.append({
            "type": "click",
            "timestamp": now.isoformat(),
            "url": url,
        })
        log.events = events
        flag_modified(log, "events")
        db.commit()

    return RedirectResponse(url=url)


@router.get("/unsubscribe/{tracking_id}")
def unsubscribe(tracking_id: str, db: Session = Depends(get_db)):
    """Unsubscribe linki: kişiyi ve sayacı güncelle."""
    log = db.query(EmailLog).filter(EmailLog.tracking_id == tracking_id).first()
    if log:
        contact = db.query(Contact).filter(Contact.id == log.contact_id).first()
        if contact and not contact.is_unsubscribed:
            contact.is_unsubscribed = True
            contact.unsubscribed_at = datetime.utcnow()
            log.status = "unsubscribed"

            campaign = db.query(Campaign).filter(Campaign.id == log.campaign_id).first()
            if campaign:
                campaign.unsubscribed_count = (campaign.unsubscribed_count or 0) + 1
            db.commit()

    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Unsubscribed</title></head>
    <body style="font-family: sans-serif; text-align: center; padding: 50px;">
        <h1>You have been unsubscribed</h1>
        <p>You will no longer receive emails from us. Thank you.</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.post("/webhook/sendgrid")
async def sendgrid_webhook(request: Request, db: Session = Depends(get_db)):
    """
    SendGrid Event Webhook.
    Bounced, delivered, spam, dropped, vb. event'leri burada yakalanır.

    SendGrid Settings > Mail Settings > Event Webhook'tan bu URL'e bağlanır:
    https://yourdomain.com/api/tracking/webhook/sendgrid
    """
    events = await request.json()

    for event in events:
        tracking_id = event.get("tracking_id")  # CustomArg'dan
        if not tracking_id:
            continue

        log = db.query(EmailLog).filter(EmailLog.tracking_id == tracking_id).first()
        if not log:
            continue

        event_type = event.get("event")
        timestamp = datetime.utcfromtimestamp(event.get("timestamp", 0))

        # Tüm event'leri kaydet
        events_list = log.events or []
        events_list.append({
            "type": event_type,
            "timestamp": timestamp.isoformat(),
            "raw": event,
        })
        log.events = events_list
        flag_modified(log, "events")

        # Status güncellemeleri
        campaign = db.query(Campaign).filter(Campaign.id == log.campaign_id).first()

        if event_type == "delivered":
            log.delivered_at = timestamp
            if log.status == "sent":
                log.status = "delivered"

        elif event_type == "bounce":
            log.bounced_at = timestamp
            log.bounce_reason = event.get("reason")
            log.status = "bounced"
            # Contact'ı işaretle
            contact = db.query(Contact).filter(Contact.id == log.contact_id).first()
            if contact:
                contact.bounce_count = (contact.bounce_count or 0) + 1
                if event.get("type") == "bounce":  # Hard bounce
                    contact.is_bounced = True
            if campaign:
                campaign.bounced_count = (campaign.bounced_count or 0) + 1

        elif event_type == "spamreport":
            log.spam_at = timestamp
            log.status = "spam"
            # Bu kullanıcı bir daha email almasın
            contact = db.query(Contact).filter(Contact.id == log.contact_id).first()
            if contact:
                contact.is_unsubscribed = True

        elif event_type == "dropped":
            log.status = "blocked"
            log.error_message = event.get("reason")

        elif event_type == "open":
            # SendGrid kendi tracking'i de varsa burada gelir, biz ayrıca pixel'le takip ediyoruz
            if not log.first_opened_at:
                log.first_opened_at = timestamp
            log.last_opened_at = timestamp

        elif event_type == "click":
            if not log.first_clicked_at:
                log.first_clicked_at = timestamp
            log.last_clicked_at = timestamp

        db.commit()

    return {"status": "ok", "processed": len(events)}
