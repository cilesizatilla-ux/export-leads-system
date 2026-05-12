"""
Wikidata SPARQL — completely free, no API key, global coverage.
Returns registered businesses by country with their websites.
Then Hunter.io finds emails per domain.
"""
import httpx
from urllib.parse import urlparse
from app.services.pdl_service import COUNTRY_TO_LANGUAGE

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
SPARQL_HEADERS = {
    "Accept": "application/sparql-results+json",
    "User-Agent": "ExportLeadsBot/1.0 (lead-generation-system)",
}

# ISO country code → Wikidata QID
_CODE_TO_QID: dict[str, str] = {
    "DE": "Q183", "AT": "Q40",  "CH": "Q39",
    "FR": "Q142", "BE": "Q31",  "NL": "Q55",  "LU": "Q32",
    "GB": "Q145", "IE": "Q27",
    "ES": "Q29",  "PT": "Q45",
    "IT": "Q38",  "GR": "Q41",
    "PL": "Q36",  "CZ": "Q213", "HU": "Q28",  "RO": "Q218",
    "SE": "Q34",  "NO": "Q20",  "DK": "Q35",  "FI": "Q33",
    "RU": "Q159", "UA": "Q212",
    "TR": "Q43",
    "US": "Q30",  "CA": "Q16",
    "MX": "Q96",  "BR": "Q155", "AR": "Q414", "CO": "Q739", "CL": "Q298",
    "CN": "Q148", "JP": "Q17",  "KR": "Q884",
    "IN": "Q668", "SG": "Q334", "MY": "Q833", "ID": "Q252", "TH": "Q869",
    "AU": "Q408", "NZ": "Q664",
    "AE": "Q878", "SA": "Q851", "EG": "Q79",  "IL": "Q801",
    "ZA": "Q258", "NG": "Q1033","KE": "Q114",
}

_TLD_TO_CODE: dict[str, str] = {
    "de": "DE", "at": "AT", "ch": "CH",
    "fr": "FR", "be": "BE", "nl": "NL",
    "gb": "GB", "uk": "GB", "ie": "IE",
    "es": "ES", "pt": "PT", "it": "IT", "gr": "GR",
    "pl": "PL", "cz": "CZ", "hu": "HU", "ro": "RO",
    "se": "SE", "no": "NO", "dk": "DK", "fi": "FI",
    "ru": "RU", "ua": "UA", "tr": "TR",
    "us": "US", "ca": "CA", "mx": "MX", "br": "BR",
    "cn": "CN", "jp": "JP", "kr": "KR",
    "in": "IN", "sg": "SG", "my": "MY", "au": "AU",
    "ae": "AE", "sa": "SA", "eg": "EG", "il": "IL",
    "za": "ZA", "ng": "NG", "ke": "KE",
}


def get_language_for_country(country_code: str) -> str:
    return COUNTRY_TO_LANGUAGE.get((country_code or "").upper(), "en")


def country_code_from_domain(domain: str, requested_countries: list[str]) -> str:
    if requested_countries and len(requested_countries) == 1:
        return requested_countries[0].upper()
    tld = (domain or "").rsplit(".", 1)[-1].lower()
    return _TLD_TO_CODE.get(tld, "")


def _domain_from_url(url: str) -> str:
    try:
        netloc = urlparse(url).netloc or url
        return netloc.replace("www.", "").strip("/").lower()
    except Exception:
        return ""


def _build_query(qid: str, terms: list[str], limit: int) -> str:
    if terms:
        conditions = " || ".join(
            f'CONTAINS(LCASE(?name), "{t.lower()[:30]}")'
            for t in terms[:6]
        )
        kw_filter = f"FILTER({conditions})"
    else:
        kw_filter = ""

    return f"""
SELECT DISTINCT ?name ?website WHERE {{
  ?company wdt:P31 wd:Q4830453 .
  ?company wdt:P17 wd:{qid} .
  ?company wdt:P856 ?website .
  ?company rdfs:label ?name FILTER(lang(?name) = "en") .
  {kw_filter}
}}
LIMIT {limit}
"""


class WikidataService:
    """Wikidata SPARQL-based company discovery — free, no API key."""

    async def discover(
        self,
        countries: list[str],
        keywords: list[str],
        industries: list[str],
        limit_per_country: int = 50,
    ) -> list[dict]:
        """
        Her ülke için Wikidata'dan şirket ve website bilgisi çeker.
        Anahtar kelime / sektör filtresi varsa SPARQL'a ekler.
        """
        terms = list(dict.fromkeys((keywords or []) + (industries or [])))
        all_results: list[dict] = []
        seen_domains: set[str] = set()

        for code in (countries or []):
            qid = _CODE_TO_QID.get(code.upper())
            if not qid:
                print(f"[Wikidata] No QID for country: {code}")
                continue

            query = _build_query(qid, terms, limit_per_country)

            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.get(
                        SPARQL_ENDPOINT,
                        params={"query": query, "format": "json"},
                        headers=SPARQL_HEADERS,
                    )
                    if resp.status_code != 200:
                        print(f"[Wikidata] {code}: HTTP {resp.status_code}")
                        continue

                    bindings = resp.json().get("results", {}).get("bindings", [])

                    for b in bindings:
                        name = b.get("name", {}).get("value", "").strip()
                        website = b.get("website", {}).get("value", "").strip()
                        domain = _domain_from_url(website)

                        if not domain or domain in seen_domains:
                            continue
                        seen_domains.add(domain)

                        all_results.append({
                            "name": name,
                            "primary_domain": domain,
                            "website_url": website,
                            "country_code": code.upper(),
                        })

            except Exception as exc:
                print(f"[Wikidata] {code} error: {exc}")
                continue

        return all_results


# Backward-compatible alias so leads.py import still works
ClearbitService = WikidataService
