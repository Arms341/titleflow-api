"""
routes/saved_sheets_export.py  v1.1.0
PDF export with agent branding (dual branding — title company + agent headshot).
v1.1.0: Look up agent from saved_sheet.agent_id, pass to PDF generator.
"""
import logging
from typing import Any, Dict

from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from models.user import User
from services.company_service import CompanyService
from services.pdf_generator import PdfGenerator, PdfGeneratorError
from services.saved_sheet_service import SavedSheetService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["saved_sheets_export"])


def _get_saved_sheet_service(db: Session = Depends(get_db)) -> SavedSheetService:
    inst = SavedSheetService()
    inst._db = db
    return inst


def _get_company_service(db: Session = Depends(get_db)) -> CompanyService:
    inst = CompanyService()
    inst._db = db
    return inst


def _get_pdf_generator() -> PdfGenerator:
    return PdfGenerator()


@router.get("/{sheet_id}/pdf")
def download_saved_sheet_pdf(
    sheet_id: int,
    db: Session = Depends(get_db),
    sheets: SavedSheetService = Depends(_get_saved_sheet_service),
    companies: CompanyService = Depends(_get_company_service),
    pdf: PdfGenerator = Depends(_get_pdf_generator),
) -> StreamingResponse:
    """GET /saved_sheets_export/{id}/pdf — branded PDF with agent headshot."""
    try:
        sheet = sheets.get_by_id(sheet_id)
        if not sheet:
            raise HTTPException(status_code=404, detail="Saved sheet not found")

        company_row = companies.get_company()
        sheet_dict: Dict[str, Any] = {
            "id": sheet.id,
            "sheet_type": sheet.sheet_type,
            "property_address": sheet.property_address,
            "property_city": getattr(sheet, "property_city", None),
            "client_name": sheet.client_name,
            "input_data": sheet.input_data,
            "output_data": sheet.output_data,
        }
        company_dict: Dict[str, Any] = {
            "company_name": company_row.company_name,
            "logo_url": company_row.logo_url,
            "primary_color": company_row.primary_color,
            "secondary_color": company_row.secondary_color,
            "phone": company_row.phone,
            "email": company_row.email,
            "website": company_row.website,
            "address": getattr(company_row, "address", None),
            "disclaimer_text": company_row.disclaimer_text,
        }

        # v1.1.0: Look up the agent who created this sheet
        agent_dict = None
        agent_id = getattr(sheet, "agent_id", None)
        if agent_id:
            try:
                agent_row = db.query(User).filter(User.id == agent_id).first()
                if agent_row:
                    agent_dict = {
                        "full_name": agent_row.full_name,
                        "phone": agent_row.phone,
                        "email": agent_row.email,
                        "avatar_url": agent_row.avatar_url,
                        "brokerage_name": getattr(agent_row, "brokerage_name", None),
                        "license_number": getattr(agent_row, "license_number", None),
                    }
            except Exception as agent_err:
                logger.warning("Could not look up agent %d: %s", agent_id, agent_err)

        buf = pdf.render_sheet(sheet_dict, company_dict, agent=agent_dict)
        filename = f"sheet_{sheet_id}.pdf"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(buf, media_type="application/pdf", headers=headers)
    except HTTPException:
        raise
    except PdfGeneratorError as e:
        logger.error("PDF generation failed: %s", str(e))
        raise HTTPException(status_code=500, detail="PDF generation failed")
    except Exception as e:
        logger.error("Error downloading PDF for sheet %d: %s", sheet_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


saved_sheets_export_router = router
