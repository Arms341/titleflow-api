"""
routes/shared.py  v1.1.0
Locked template — JARVIS title_company gig.
Public share endpoint — no auth required.

v1.1.0: Added POST /shared/{token}/sign — client e-signature capture.
v1.0.0: Initial public share view.
"""
import logging
from datetime import datetime
from typing import Any, Dict

from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.company_service import CompanyService
from services.saved_sheet_service import SavedSheetService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["shared"])


class SignaturePayload(BaseModel):
    """Client signature submission."""
    signature: str  # base64 PNG data URL
    signer_name: str = ""


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
                "is_signed": sheet.client_signature is not None,
                "signed_at": sheet.signed_at.isoformat() if sheet.signed_at else None,
                "created_at": sheet.created_at.isoformat() if sheet.created_at else None,
            },
            "branding": {
                "company_name": company.company_name,
                "logo_url": company.logo_url,
                "primary_color": company.primary_color,
                "secondary_color": getattr(company, "secondary_color", None),
                "phone": company.phone,
                "email": getattr(company, "email", None),
                "website": getattr(company, "website", None),
                "tagline": getattr(company, "tagline", None),
                "disclaimer_text": getattr(company, "disclaimer_text", None),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching shared sheet %s: %s", share_token, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{share_token}/sign")
def sign_shared_sheet(
    share_token: str,
    payload: SignaturePayload,
    db: Session = Depends(get_db),
    sheets: SavedSheetService = Depends(_get_saved_sheet_service),
) -> Dict[str, Any]:
    """POST /shared/{token}/sign — client signs the shared sheet."""
    try:
        sheet = sheets.get_by_share_token(share_token)
        if not sheet:
            raise HTTPException(status_code=404, detail="Share link not found")
        if not sheet.is_shared:
            raise HTTPException(status_code=404, detail="Share link inactive")
        if sheet.client_signature:
            raise HTTPException(status_code=400, detail="Sheet already signed")

        sheet.client_signature = payload.signature
        sheet.signed_at = datetime.utcnow()
        if payload.signer_name and not sheet.client_name:
            sheet.client_name = payload.signer_name
        db.commit()
        db.refresh(sheet)

        logger.info(f"[SHARED] Sheet {sheet.id} signed via token {share_token[:8]}...")
        return {
            "status": "signed",
            "signed_at": sheet.signed_at.isoformat(),
            "message": "Thank you! Your signature has been recorded.",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error signing shared sheet %s: %s", share_token, str(e))
        raise HTTPException(status_code=500, detail="Signature failed")


shared_router = router  # FIX-ROUTER-ALIAS
