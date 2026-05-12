"""
People Data Labs (PDL) API entegrasyonu — Apollo.io'nun ücretsiz alternatifi.
Ücretsiz plan: 500 API kredisi (https://www.peopledatalabs.com/signup).
API dokümantasyonu: https://docs.peopledatalabs.com
"""
import httpx
from typing import Optional

from app.core.config import settings


# ISO ülke kodu → PDL'in beklediği küçük harfli ülke adı
_CODE_TO_NAME: dict[str, str] = {
    "DE": "germany", "AT": "austria", "CH": "switzerland",
    "FR": "france", "BE": "belgium", "LU": "luxembourg",
    "ES": "spain", "MX": "mexico", "AR": "argentina", "CO": "colombia", "CL": "chile",
    "IT": "italy",
    "PT": "portugal", "BR": "brazil",
    "NL": "netherlands",
    "PL": "poland",
    "RU": "russia", "BY": "belarus", "KZ": "kazakhstan",
    "TR": "turkey",
    "JP": "japan",
    "CN": "china", "TW": "taiwan", "HK": "hong kong",
    "KR": "south korea",
    "SA": "saudi arabia", "AE": "united arab emirates", "EG": "egypt",
    "US": "united states", "GB": "united kingdom", "CA": "canada",
    "AU": "australia", "IN": "india",
    "ZA": "south africa", "NG": "nigeria", "KE": "kenya",
    "TH": "thailand", "VN": "vietnam", "ID": "indonesia", "MY": "malaysia",
    "SG": "singapore", "PH": "philippines",
    "SE": "sweden", "NO": "norway", "DK": "denmark", "FI": "finland",
    "CZ": "czech republic", "HU": "hungary", "RO": "romania", "GR": "greece",
    "UA": "ukraine", "IL": "israel",
}

# ISO ülke kodu → dil kodu (Apollo'dan taşındı)
COUNTRY_TO_LANGUAGE: dict[str, str] = {
    "DE": "de", "AT": "de", "CH": "de",
    "FR": "fr", "BE": "fr", "LU": "fr",
    "ES": "es", "MX": "es", "AR": "es", "CO": "es", "CL": "es",
    "IT": "it",
    "PT": "pt", "BR": "pt",
    "NL": "nl",
    "PL": "pl",
    "RU": "ru", "BY": "ru", "KZ": "ru",
    "TR": "tr",
    "JP": "ja",
    "CN": "zh", "TW": "zh", "HK": "zh",
    "KR": "ko",
    "SA": "ar", "AE": "ar", "EG": "ar",
}


def get_language_for_country(country_code: str) -> str:
    """Ülke koduna göre dil kodunu döndür. Bilinmeyenler için 'en'."""
    if not country_code:
        return "en"
    return COUNTRY_TO_LANGUAGE.get(country_code.upper(), "en")


_NAME_TO_CODE: dict[str, str] = {v: k for k, v in _CODE_TO_NAME.items()}


def _country_name(code: str) -> Optional[str]:
    return _CODE_TO_NAME.get((code or "").upper())


def country_name_to_code(name: str) -> str:
    """PDL country name → ISO-2 code. Returns '' if unknown."""
    return _NAME_TO_CODE.get((name or "").lower(), "")


def _clean_domain(url: str) -> str:
    return url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]


class PDLService:
    BASE_URL = "https://api.peopledatalabs.com/v5"

    def __init__(self):
        if not settings.PDL_API_KEY:
            raise ValueError(
                "PDL_API_KEY ayarlanmamış. "
                "https://www.peopledatalabs.com/signup adresinden ücretsiz hesap oluşturun "
                "ve .env dosyasına PDL_API_KEY= ekleyin."
            )
        self.headers = {
            "Content-Type": "application/json",
            "X-Api-Key": settings.PDL_API_KEY,
        }

    async def search_organizations(
        self,
        keywords: Optional[list[str]] = None,
        countries: Optional[list[str]] = None,
        industries: Optional[list[str]] = None,
        employee_ranges: Optional[list[str]] = None,
        page: int = 1,
        per_page: int = 25,
    ) -> dict:
        """
        Şirket arama. Apollo-compatible çıktı döndürür:
        {"organizations": [...], "total_organizations": N}
        """
        url = f"{self.BASE_URL}/company/search"
        must: list[dict] = []

        if keywords:
            should = [{"match": {"name": kw}} for kw in keywords]
            should += [{"match": {"industry": kw}} for kw in keywords]
            should += [{"match": {"tags": kw}} for kw in keywords]
            should += [{"match": {"summary": kw}} for kw in keywords]
            must.append({"bool": {"should": should}})

        if countries:
            names = [_country_name(c) for c in countries]
            names = [n for n in names if n]
            if names:
                must.append({"terms": {"location.country": names}})

        if industries:
            must.append({"terms": {"industry": [i.lower() for i in industries]}})

        if employee_ranges:
            for r in employee_ranges:
                parts = r.split(",")
                if len(parts) == 2:
                    try:
                        must.append({
                            "range": {
                                "employee_count": {
                                    "gte": int(parts[0]),
                                    "lte": int(parts[1]),
                                }
                            }
                        })
                    except ValueError:
                        pass
                    break

        payload = {
            "query": {"bool": {"must": must}} if must else {"match_all": {}},
            "size": per_page,
            "from": (page - 1) * per_page,
            "dataset": "all",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()

        organizations = []
        for c in result.get("data", []):
            location = c.get("location") or {}
            raw_website = c.get("website") or ""
            domain = c.get("domain") or (_clean_domain(raw_website) if raw_website else None)

            phone_numbers = c.get("phone_numbers") or []
            phone = phone_numbers[0] if phone_numbers else None

            raw_country = location.get("country") or c.get("country") or ""
            organizations.append({
                "id": c.get("id"),
                "name": c.get("name") or c.get("display_name"),
                "primary_domain": domain or None,
                "website_url": raw_website or None,
                "country": raw_country,
                "country_code": country_name_to_code(raw_country),
                "city": location.get("locality"),
                "industry": c.get("industry"),
                "estimated_num_employees": c.get("employee_count"),
                "phone": phone,
                "linkedin_url": c.get("linkedin_url"),
            })

        return {
            "organizations": organizations,
            "total_organizations": result.get("total", 0),
        }

    async def search_people(
        self,
        organization_ids: Optional[list[str]] = None,
        organization_domains: Optional[list[str]] = None,
        titles: Optional[list[str]] = None,
        seniorities: Optional[list[str]] = None,
        countries: Optional[list[str]] = None,
        page: int = 1,
        per_page: int = 25,
    ) -> dict:
        """
        Kişi arama. Apollo-compatible çıktı döndürür:
        {"people": [...]}
        Domain ile arama, ID ile aramadan daha güvenilirdir.
        """
        url = f"{self.BASE_URL}/person/search"
        must: list[dict] = []

        if organization_ids:
            must.append({"terms": {"job_company_id": organization_ids}})

        if organization_domains:
            clean = [_clean_domain(d) for d in organization_domains if d]
            if clean:
                must.append({"terms": {"job_company_website": clean}})

        if titles:
            should = [{"match": {"job_title": t}} for t in titles]
            must.append({"bool": {"should": should}})

        if seniorities:
            must.append({"terms": {"job_title_levels": seniorities}})

        if countries:
            names = [_country_name(c) for c in countries]
            names = [n for n in names if n]
            if names:
                must.append({"terms": {"location_country": names}})

        payload = {
            "query": {"bool": {"must": must}} if must else {"match_all": {}},
            "size": per_page,
            "from": (page - 1) * per_page,
            "dataset": "all",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()

        people = []
        for p in result.get("data", []):
            # work_email öncelikli; yoksa professional olarak işaretlenmiş ilk email
            email = p.get("work_email")
            if not email:
                for e in p.get("emails") or []:
                    if isinstance(e, dict) and e.get("type") == "professional":
                        email = e.get("address")
                        break

            phone_numbers = p.get("phone_numbers") or []

            people.append({
                "id": p.get("id"),
                "first_name": p.get("first_name"),
                "last_name": p.get("last_name"),
                "name": p.get("full_name"),
                "title": p.get("job_title"),
                "email": email,
                "phone_numbers": [{"raw_number": ph} for ph in phone_numbers],
                "linkedin_url": p.get("linkedin_url"),
            })

        return {"people": people}
