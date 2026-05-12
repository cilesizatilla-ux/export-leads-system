"""
Claude AI ile email içeriği üretimi.
- Şablon yazma
- Şirkete özel kişiselleştirme
- Açılmayan emaillere yeni strateji önerme
"""
from anthropic import Anthropic
from typing import Optional

from app.core.config import settings


class AIContentService:
    MODEL = "claude-sonnet-4-6"

    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY ayarlanmamış")
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def generate_cold_email(
        self,
        company_name: str,
        company_industry: str,
        company_country: str,
        contact_name: Optional[str],
        contact_title: Optional[str],
        my_company_name: str,
        my_products: str,
        my_value_proposition: str,
        tone: str = "professional",
        language: str = "en",
    ) -> dict:
        """
        Şirkete ve kişiye özel cold email yaz.
        Çıktı: {"subject": "...", "body": "..."} (HTML)
        """
        prompt = f"""Sen profesyonel bir B2B satış uzmanısın.
Aşağıdaki bilgilerle kısa, etkili bir cold email yaz.

HEDEF ŞİRKET:
- İsim: {company_name}
- Sektör: {company_industry}
- Ülke: {company_country}

HEDEF KİŞİ:
- İsim: {contact_name or "Sayın Yetkili"}
- Pozisyon: {contact_title or "Decision Maker"}

BİZİM ŞİRKETİMİZ:
- İsim: {my_company_name}
- Ürünlerimiz: {my_products}
- Değer önerisi: {my_value_proposition}

GEREKSİNİMLER:
- Dil: {language}
- Ton: {tone}
- Maks 150 kelime
- Kişisel bir hook ile başla (şirketinin sektörü/ülkesi)
- Net bir CTA (call-to-action) içersin (15 dakikalık görüşme önerisi)
- HTML formatında body (paragraf, varsa <strong>, <a> kullanabilirsin)
- Subject satırı meraklı olsun, satışçı tonu olmasın
- Spam tetikleyici kelimelerden kaçın (FREE!, BUY NOW, !!! vb.)

ÇIKTI FORMATI (KESİN JSON):
{{"subject": "...", "body": "<p>...</p>"}}

Sadece JSON döndür, başka açıklama yapma."""

        response = self.client.messages.create(
            model=self.MODEL,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        # JSON parse'a hazırla
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        import json
        return json.loads(text)

    def suggest_followup_strategy(
        self,
        original_subject: str,
        original_body: str,
        opened: bool,
        clicked: bool,
        days_since_sent: int,
        followup_number: int,
    ) -> dict:
        """
        Açılmayan/yanıtlanmayan emaillere yeni içerik öner.
        Çıktı: {"subject": "...", "body": "...", "strategy_note": "..."}
        """
        engagement = "açıldı ama tıklanmadı" if opened and not clicked else (
            "açılmadı bile" if not opened else "tıklandı ama yanıt gelmedi"
        )

        prompt = f"""Cold email kampanyası takip stratejisi öner.

ÖNCEKI EMAIL:
- Konu: {original_subject}
- Gövde: {original_body}

DURUM:
- Email durumu: {engagement}
- Gönderimden bu yana: {days_since_sent} gün
- Bu kaçıncı takip: {followup_number}/3

YENİ EMAIL STRATEJISI:
- Önceki ile farklı bir açıdan yaklaş
- Subject satırı tamamen farklı olsun
- Daha kısa ve daha net olsun
- Yeni bir değer/içgörü/case study ekle
- HTML body kullan

ÇIKTI (JSON):
{{
  "subject": "...",
  "body": "<p>...</p>",
  "strategy_note": "Bu takipte hangi yaklaşımı kullandığının kısa özeti"
}}

Sadece JSON döndür."""

        response = self.client.messages.create(
            model=self.MODEL,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        import json
        return json.loads(text)

    def check_spam_risk(self, subject: str, body: str) -> dict:
        """Email içeriğinin spam riskini analiz et, iyileştirme öner."""
        prompt = f"""Aşağıdaki cold emaili spam tetikleyici açısından analiz et.

KONU: {subject}
GÖVDE: {body}

Kontrol edilecekler:
1. Spam kelimeleri (FREE, BUY NOW, GUARANTEED, $$$, vb.)
2. Aşırı büyük harf kullanımı
3. Aşırı ünlem işareti
4. Şüpheli linkler
5. Spam-y subject kalıpları
6. Text/link oranı

ÇIKTI (JSON):
{{
  "risk_score": 0-100 arası sayı,
  "issues": ["sorun 1", "sorun 2"],
  "suggestions": ["öneri 1", "öneri 2"],
  "improved_subject": "düzeltilmiş konu",
  "improved_body": "düzeltilmiş gövde HTML"
}}

Sadece JSON döndür."""

        response = self.client.messages.create(
            model=self.MODEL,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        import json
        return json.loads(text)
