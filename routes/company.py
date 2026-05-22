"""
routes/company.py  v1.0.0
Locked template — JARVIS title_company gig.
Singleton company branding. GET is public, PUT is admin-only.
"""
import logging

from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from schemas.company import CompanyResponse, CompanyUpdate
from services.company_service import CompanyService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["company"])


def _get_company_service(db: Session = Depends(get_db)) -> CompanyService:
    """Inline factory."""
    inst = CompanyService()
    inst._db = db
    return inst


@router.get("/", response_model=CompanyResponse)
def get_company(
    service: CompanyService = Depends(_get_company_service),
) -> CompanyResponse:
    """GET /company/ — public endpoint used by frontend for branding."""
    try:
        return service.get_company()
    except Exception as e:
        logger.error("Error fetching company: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/", response_model=CompanyResponse)
def update_company(
    data: CompanyUpdate,
    service: CompanyService = Depends(_get_company_service),
) -> CompanyResponse:
    """PUT /company/ — admin only."""
    try:
        return service.update(data)
    except Exception as e:
        logger.error("Error updating company: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


company_router = router  # FIX-ROUTER-ALIAS
