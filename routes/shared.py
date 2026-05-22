"""
routes/shared.py  v1.0.0
Locked template — JARVIS title_company gig.
Public share endpoint — no auth required. This is the viral lead-gen
mechanism: agents share a saved sheet link with clients, and each view
is a branded impression of the title company.
"""
import logging
from typing import Any, Dict

from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from services.company_service import CompanyService
from services.saved_sheet_service import SavedSheetService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["shared"])


def _get_saved_sheet_service(db: Session = Depends(get_db)) -> SavedSheetService:
    """Inline factory."""
    inst = SavedSheetService()
    inst._db = db
    return inst


def _get_company_service(db: Session = Depends(get_db)) -> CompanyService:
    """Inline factory."""
    inst = CompanyService()
    inst._db = db
    return inst


@router.get("/{share_token}")
def get_shared_sheet(
    share_token: str,
    sheets: SavedSheetService = Depends(_get_saved_sheet_service),
    companies: CompanyService = Depends(_get_company_service),
) -> Dict[str, Any]:
    """GET /shared/{token} — public branded sheet view. No auth."""
    try:
        sheet = sheets.get_by_share_token(share_token)
        if not sheet:
            raise HTTPException(status_code=404, detail="Share link not found")
        if not sheet.is_shared:
            raise HTTPException(status_code=404, detail="Share link inactive")

        company = companies.get_company()

        return {
            "sheet": {
                "id": sheet.id,
                "sheet_type": sheet.sheet_type,
                "property_address": sheet.property_address,
                "property_city": sheet.property_city,
                "client_name": sheet.client_name,
                "input_data": sheet.input_data,
                "output_data": sheet.output_data,
                "created_at": sheet.created_at.isoformat() if sheet.created_at else None,
            },
            "branding": {
                "company_name": company.company_name,
                "logo_url": company.logo_url,
                "primary_color": company.primary_color,
                "secondary_color": company.secondary_color,
                "phone": company.phone,
                "email": company.email,
                "website": company.website,
                "tagline": company.tagline,
                "disclaimer_text": company.disclaimer_text,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching shared sheet %s: %s", share_token, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


shared_router = router  # FIX-ROUTER-ALIAS
