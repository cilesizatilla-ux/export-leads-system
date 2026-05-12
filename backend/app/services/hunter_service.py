"""
Hunter.io API entegrasyonu.
Domain bazlı email bulma, email doğrulama.

Doküman: https://hunter.io/api-documentation/v2
"""
import httpx
from typing import Optional

from app.core.config import settings


class HunterService:
    BASE_URL = "https://api.hunter.io/v2"

    def __init__(self):
        if not settings.HUNTER_API_KEY:
            raise ValueError("HUNTER_API_KEY ayarlanmamış")
        self.api_key = settings.HUNTER_API_KEY

    async def domain_search(
        self,
        domain: str,
        limit: int = 25,
        department: Optional[str] = None,
        seniority: Optional[str] = None,
    ) -> dict:
        """
        Bir domaindeki tüm public email adreslerini bul.

        Args:
            domain: Şirket alanı (örn: "siemens.com")
            department: "executive", "purchasing", "sales", "marketing"
            seniority: "junior", "senior", "executive"
        """
        url = f"{self.BASE_URL}/domain-search"
        params = {
            "domain": domain,
            "api_key": self.api_key,
            "limit": limit,
        }
        if department:
            params["department"] = department
        if seniority:
            params["seniority"] = seniority

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def email_finder(
        self,
        domain: str,
        first_name: str,
        last_name: str,
    ) -> dict:
        """İsim+domain'den email tahmini."""
        url = f"{self.BASE_URL}/email-finder"
        params = {
            "domain": domain,
            "first_name": first_name,
            "last_name": last_name,
            "api_key": self.api_key,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def email_verifier(self, email: str) -> dict:
        """
        Email adresini doğrula. Spam'e düşmeyi önler.

        Returns: result = "deliverable" | "undeliverable" | "risky" | "unknown"
        """
        url = f"{self.BASE_URL}/email-verifier"
        params = {"email": email, "api_key": self.api_key}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
