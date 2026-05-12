"""
DeepL API entegrasyonu - profesyonel kalitede çeviri.
HTML formatlamayı koruyarak çevirir (önemli: email body'sinde HTML var).
"""
import deepl
from typing import Optional

from app.core.config import settings


# DeepL'in desteklediği hedef diller (ihtiyaca göre genişletilebilir)
SUPPORTED_LANGUAGES = {
    "en": "EN-US",
    "de": "DE",
    "fr": "FR",
    "es": "ES",
    "it": "IT",
    "pt": "PT-PT",
    "nl": "NL",
    "pl": "PL",
    "ru": "RU",
    "tr": "TR",
    "ja": "JA",
    "zh": "ZH",
    "ko": "KO",
    "ar": "AR",
}


class TranslationService:
    def __init__(self):
        if not settings.DEEPL_API_KEY:
            raise ValueError("DEEPL_API_KEY ayarlanmamış")
        self.translator = deepl.Translator(settings.DEEPL_API_KEY)

    def translate_text(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        preserve_formatting: bool = True,
    ) -> str:
        """Düz metin çevirisi."""
        target = SUPPORTED_LANGUAGES.get(target_lang.lower(), "EN-US")
        source = SUPPORTED_LANGUAGES.get(source_lang.lower()) if source_lang else None
        if source:
            source = source.split("-")[0]  # DeepL kaynak dil için "EN-US" değil "EN" ister

        result = self.translator.translate_text(
            text,
            target_lang=target,
            source_lang=source,
            preserve_formatting=preserve_formatting,
        )
        return result.text

    def translate_html(
        self,
        html: str,
        target_lang: str,
        source_lang: Optional[str] = None,
    ) -> str:
        """HTML formatını koruyarak çeviri (email body için)."""
        target = SUPPORTED_LANGUAGES.get(target_lang.lower(), "EN-US")
        source = SUPPORTED_LANGUAGES.get(source_lang.lower()) if source_lang else None
        if source:
            source = source.split("-")[0]

        result = self.translator.translate_text(
            html,
            target_lang=target,
            source_lang=source,
            tag_handling="html",     # HTML etiketlerini bozma
            preserve_formatting=True,
        )
        return result.text

    def translate_email(
        self,
        subject: str,
        body_html: str,
        target_lang: str,
        source_lang: str = "en",
    ) -> dict:
        """Bir email paketinin (konu + gövde) komple çevirisi."""
        return {
            "subject": self.translate_text(subject, target_lang, source_lang),
            "body": self.translate_html(body_html, target_lang, source_lang),
            "language": target_lang,
        }

    def get_usage(self) -> dict:
        """Aylık çeviri kotası kontrolü."""
        usage = self.translator.get_usage()
        return {
            "character_count": usage.character.count,
            "character_limit": usage.character.limit,
        }
