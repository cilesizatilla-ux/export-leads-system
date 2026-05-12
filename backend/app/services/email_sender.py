"""
SendGrid ile email gönderme servisi.
- Tracking pixel ekleme (açılma takibi)
- Link rewriting (tıklama takibi)
- PDF/sunum eki ekleme
- Unsubscribe linki ekleme
"""
import base64
import os
import secrets
from typing import Optional
from email.utils import formataddr

import sendgrid
from sendgrid.helpers.mail import (
    Mail, Email, To, Content, Attachment, FileContent,
    FileName, FileType, Disposition, TrackingSettings,
    ClickTracking, OpenTracking, CustomArg,
)

from app.core.config import settings


def generate_tracking_id() -> str:
    """Benzersiz tracking ID üret (email loglarında ve URL'lerde kullanılır)."""
    return secrets.token_urlsafe(32)


def inject_tracking_pixel(html_body: str, tracking_id: str) -> str:
    """
    Email body'sine 1x1 transparent tracking pixel ekle.
    Email açıldığında bu image yüklendiğinde sunucumuza istek gelir.
    """
    pixel_url = f"{settings.TRACKING_BASE_URL}/api/tracking/pixel/{tracking_id}.gif"
    pixel_html = (
        f'<img src="{pixel_url}" width="1" height="1" alt="" '
        f'style="display:none;border:0;width:1px;height:1px;" />'
    )
    # </body> önüne ekle, yoksa sonuna ekle
    if "</body>" in html_body.lower():
        idx = html_body.lower().rfind("</body>")
        return html_body[:idx] + pixel_html + html_body[idx:]
    return html_body + pixel_html


def inject_unsubscribe_footer(html_body: str, tracking_id: str, language: str = "en") -> str:
    """Email sonuna unsubscribe linki ekle (yasal zorunluluk)."""
    unsubscribe_url = f"{settings.TRACKING_BASE_URL}/api/tracking/unsubscribe/{tracking_id}"

    # Çok dilli unsubscribe metinleri
    texts = {
        "en": "If you don't want to receive these emails, you can",
        "de": "Wenn Sie diese E-Mails nicht mehr erhalten möchten,",
        "fr": "Si vous ne souhaitez plus recevoir ces e-mails, vous pouvez",
        "es": "Si no desea recibir estos correos, puede",
        "it": "Se non desideri ricevere queste email, puoi",
        "pt": "Se não quiser receber estes e-mails, pode",
        "tr": "Bu e-postaları almak istemiyorsanız",
        "ru": "Если вы не хотите получать эти письма, вы можете",
        "ja": "これらのメールの受信を希望されない場合は、",
        "zh": "如果您不希望收到这些邮件，您可以",
    }
    unsub_label = {
        "en": "unsubscribe here",
        "de": "hier abmelden",
        "fr": "vous désabonner ici",
        "es": "darse de baja aquí",
        "it": "annullare l'iscrizione qui",
        "pt": "cancelar a inscrição aqui",
        "tr": "buradan abonelikten çıkabilirsiniz",
        "ru": "отписаться здесь",
        "ja": "こちらから登録解除できます",
        "zh": "在此退订",
    }
    text = texts.get(language, texts["en"])
    label = unsub_label.get(language, unsub_label["en"])

    footer = (
        f'<hr style="border:none;border-top:1px solid #eee;margin:24px 0;" />'
        f'<p style="font-size:11px;color:#888;text-align:center;">'
        f'{text} <a href="{unsubscribe_url}" style="color:#888;">{label}</a>.'
        f'</p>'
    )
    if "</body>" in html_body.lower():
        idx = html_body.lower().rfind("</body>")
        return html_body[:idx] + footer + html_body[idx:]
    return html_body + footer


class EmailSenderService:
    def __init__(self):
        if not settings.SENDGRID_API_KEY:
            raise ValueError("SENDGRID_API_KEY ayarlanmamış")
        self.client = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)

    def send_email(
        self,
        to_email: str,
        to_name: Optional[str],
        subject: str,
        html_body: str,
        tracking_id: str,
        language: str = "en",
        attachment_path: Optional[str] = None,
        attachment_name: Optional[str] = None,
        campaign_id: Optional[int] = None,
    ) -> dict:
        """
        Tek bir email gönder. Tracking ve unsubscribe otomatik enjekte edilir.

        Returns: {"success": bool, "message_id": str, "error": str}
        """
        # Tracking ve unsubscribe enjeksiyonu
        html_body = inject_unsubscribe_footer(html_body, tracking_id, language)
        html_body = inject_tracking_pixel(html_body, tracking_id)

        message = Mail(
            from_email=Email(settings.SENDER_EMAIL, settings.SENDER_NAME),
            to_emails=To(to_email, to_name) if to_name else To(to_email),
            subject=subject,
            html_content=Content("text/html", html_body),
        )

        # Tracking ayarları (SendGrid kendi tracking'i de var)
        tracking = TrackingSettings()
        tracking.click_tracking = ClickTracking(enable=True, enable_text=False)
        tracking.open_tracking = OpenTracking(enable=True)
        message.tracking_settings = tracking

        # Custom arguments (webhook'larda hangi log olduğunu bulmak için)
        message.add_custom_arg(CustomArg("tracking_id", tracking_id))
        if campaign_id:
            message.add_custom_arg(CustomArg("campaign_id", str(campaign_id)))

        # PDF/sunum eki
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                file_data = base64.b64encode(f.read()).decode()

            attachment = Attachment(
                FileContent(file_data),
                FileName(attachment_name or os.path.basename(attachment_path)),
                FileType("application/pdf"),
                Disposition("attachment"),
            )
            message.attachment = attachment

        try:
            response = self.client.send(message)
            message_id = response.headers.get("X-Message-Id", "")
            return {
                "success": True,
                "message_id": message_id,
                "status_code": response.status_code,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
