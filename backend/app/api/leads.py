"""
Lead Generation API'leri.
PDL'den şirket bul, Hunter'dan email bul, DB'ye kaydet, listele.
"""
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company
from app.models.contact import Contact
from app.schemas.schemas import (
    LeadSearchRequest, LeadSearchResponse,
    CompanyResponse, ContactResponse,
)
from app.services.pdl_service import PDLService, get_language_for_country
from app.services.hunter_service import HunterService

router = APIRouter(prefix="/api/leads", tags=["Leads"])


@router.post("/search/apollo", response_model=LeadSearchResponse)
async def search_apollo(request: LeadSearchRequest, db: Session = Depends(get_db)):
    """
    Apollo.io üzerinden şirket arama.
    Bulunan şirketler ve kişiler DB'ye kaydedilir.
    """
    try:
        pdl = PDLService()
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # 1) Şirketleri bul
    try:
        companies_data = await pdl.search_organizations(
            keywords=request.keywords,
            countries=request.countries,
            industries=request.industries,
            employee_ranges=request.employee_ranges,
            page=request.page,
            per_page=request.per_page,
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"PDL API hatası: {e.response.text}")

    organizations = companies_data.get("organizations", [])
    if not organizations:
        return LeadSearchResponse(total_found=0, saved_count=0, companies=[])

    saved_companies = []

    for org in organizations:
        country_code = org.get("country_code") or (org.get("country") or "").upper()[:2]
        language = get_language_for_country(country_code)

        # Daha önce kaydedildi mi?
        existing = db.query(Company).filter(
            Company.domain == org.get("primary_domain")
        ).first()

        if existing:
            saved_companies.append(existing)
            continue

        if not request.save_to_db:
            continue

        company = Company(
            name=org.get("name"),
            domain=org.get("primary_domain"),
            website=org.get("website_url"),
            country=org.get("country"),
            country_code=country_code,
            language=language,
            city=org.get("city"),
            industry=org.get("industry"),
            employee_count=str(org.get("estimated_num_employees", "")),
            phone=org.get("phone"),
            source="apollo",
            source_id=org.get("id"),
            raw_data=org,
        )
        db.add(company)
        db.flush()

        # 2) Hunter ile domain'den email bul (PDL ücretsiz planda email vermez)
        domain = org.get("primary_domain")
        if domain and request.save_to_db:
            try:
                hunter = HunterService()
                hunter_data = await hunter.domain_search(domain=domain, limit=5)
                for email_record in hunter_data.get("data", {}).get("emails", []):
                    email = email_record.get("value")
                    if not email:
                        continue
                    if db.query(Contact).filter(Contact.email == email).first():
                        continue
                    contact = Contact(
                        company_id=company.id,
                        first_name=email_record.get("first_name"),
                        last_name=email_record.get("last_name"),
                        full_name=f"{email_record.get('first_name') or ''} {email_record.get('last_name') or ''}".strip() or None,
                        title=email_record.get("position"),
                        department=email_record.get("department"),
                        email=email,
                        email_status=email_record.get("verification", {}).get("status"),
                        linkedin_url=email_record.get("linkedin"),
                        source="hunter",
                    )
                    db.add(contact)
            except Exception as e:
                print(f"Hunter email araması hata ({domain}): {e}")

        saved_companies.append(company)

    db.commit()

    return LeadSearchResponse(
        total_found=len(organizations),
        saved_count=len(saved_companies),
        companies=[CompanyResponse.model_validate(c) for c in saved_companies],
    )


@router.post("/search/hunter")
async def search_hunter(domain: str, limit: int = 25, db: Session = Depends(get_db)):
    """Hunter.io ile bir domain'in tüm public emaillerini bul."""
    try:
        hunter = HunterService()
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    try:
        result = await hunter.domain_search(domain=domain, limit=limit)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Hunter API hatası: {e.response.text}")
    data = result.get("data", {})

    # Şirket kaydı (yoksa oluştur)
    company = db.query(Company).filter(Company.domain == domain).first()
    if not company:
        company = Company(
            name=data.get("organization") or domain,
            domain=domain,
            country=data.get("country"),
            country_code=(data.get("country") or "")[:2].upper(),
            language=get_language_for_country((data.get("country") or "")[:2].upper()),
            source="hunter",
            raw_data=data,
        )
        db.add(company)
        db.flush()

    saved_contacts = []
    for email_record in data.get("emails", []):
        email = email_record.get("value")
        if not email:
            continue

        existing = db.query(Contact).filter(Contact.email == email).first()
        if existing:
            saved_contacts.append(existing)
            continue

        contact = Contact(
            company_id=company.id,
            first_name=email_record.get("first_name"),
            last_name=email_record.get("last_name"),
            full_name=f"{email_record.get('first_name', '')} {email_record.get('last_name', '')}".strip(),
            title=email_record.get("position"),
            department=email_record.get("department"),
            email=email,
            email_status=email_record.get("verification", {}).get("status"),
            phone=email_record.get("phone_number"),
            linkedin_url=email_record.get("linkedin"),
            source="hunter",
        )
        db.add(contact)
        saved_contacts.append(contact)

    db.commit()

    return {
        "company": CompanyResponse.model_validate(company),
        "contacts_count": len(saved_contacts),
        "contacts": [
            {"email": c.email, "name": c.full_name, "title": c.title}
            for c in saved_contacts
        ],
    }


@router.get("/companies", response_model=list[CompanyResponse])
def list_companies(
    country_code: str = Query(None),
    industry: str = Query(None),
    trade_type: str = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Kayıtlı şirketleri listele (filtre desteği ile)."""
    query = db.query(Company)
    if country_code:
        query = query.filter(Company.country_code == country_code.upper())
    if industry:
        query = query.filter(Company.industry.ilike(f"%{industry}%"))
    if trade_type:
        query = query.filter(Company.trade_type == trade_type)

    return query.offset(skip).limit(limit).all()


@router.get("/contacts", response_model=list[ContactResponse])
def list_contacts(
    company_id: int = Query(None),
    country_code: str = Query(None),
    only_active: bool = Query(True, description="Bounce/unsubscribe olanları hariç tut"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Kayıtlı kişileri listele."""
    query = db.query(Contact)

    if company_id:
        query = query.filter(Contact.company_id == company_id)
    if country_code:
        query = query.join(Company).filter(Company.country_code == country_code.upper())
    if only_active:
        query = query.filter(
            Contact.is_unsubscribed == False,  # noqa
            Contact.is_bounced == False,
        )

    return query.offset(skip).limit(limit).all()


@router.get("/stats")
def get_lead_stats(db: Session = Depends(get_db)):
    """Toplam istatistikler."""
    total_companies = db.query(Company).count()
    total_contacts = db.query(Contact).count()
    active_contacts = db.query(Contact).filter(
        Contact.is_unsubscribed == False,  # noqa
        Contact.is_bounced == False,
    ).count()

    # Ülke dağılımı
    from sqlalchemy import func
    country_dist = db.query(
        Company.country_code,
        func.count(Company.id).label("count"),
    ).group_by(Company.country_code).order_by(func.count(Company.id).desc()).limit(20).all()

    return {
        "total_companies": total_companies,
        "total_contacts": total_contacts,
        "active_contacts": active_contacts,
        "country_distribution": [
            {"country_code": c[0], "count": c[1]} for c in country_dist
        ],
    }
