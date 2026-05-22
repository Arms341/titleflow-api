"""
routes/saved_sheets.py  v1.0.0
Locked template — JARVIS title_company gig.
Saved sheet CRUD + share token generation + public share route.
"""
import logging
from typing import List, Optional

from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from schemas.saved_sheet import (
    SavedSheetCreate,
    SavedSheetResponse,
    SavedSheetUpdate,
    ShareResponse,
)
from services.saved_sheet_service import SavedSheetService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["saved_sheets"])


def _get_saved_sheet_service(db: Session = Depends(get_db)) -> SavedSheetService:
    """Inline factory."""
    inst = SavedSheetService()
    inst._db = db
    return inst


@router.get("/", response_model=List[SavedSheetResponse])
def list_saved_sheets(
    skip: int = 0,
    limit: int = 100,
    sheet_type: Optional[str] = Query(None),
    service: SavedSheetService = Depends(_get_saved_sheet_service),
) -> List[SavedSheetResponse]:
    """GET /saved-sheets/."""
    try:
        return service.list_all(skip=skip, limit=limit, sheet_type=sheet_type)
    except Exception as e:
        logger.error("Error listing saved_sheets: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{sheet_id}", response_model=SavedSheetResponse)
def get_saved_sheet(
    sheet_id: int,
    service: SavedSheetService = Depends(_get_saved_sheet_service),
) -> SavedSheetResponse:
    """GET /saved-sheets/{id}."""
    try:
        sheet = service.get_by_id(sheet_id)
        if not sheet:
            raise HTTPException(status_code=404, detail="Saved sheet not found")
        return sheet
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching saved_sheet %d: %s", sheet_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=SavedSheetResponse, status_code=201)
def create_saved_sheet(
    data: SavedSheetCreate,
    service: SavedSheetService = Depends(_get_saved_sheet_service),
) -> SavedSheetResponse:
    """POST /saved-sheets/."""
    try:
        return service.create(data)
    except Exception as e:
        logger.error("Error creating saved_sheet: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{sheet_id}", response_model=SavedSheetResponse)
def update_saved_sheet(
    sheet_id: int,
    data: SavedSheetUpdate,
    service: SavedSheetService = Depends(_get_saved_sheet_service),
) -> SavedSheetResponse:
    """PUT /saved-sheets/{id}."""
    try:
        updated = service.update(sheet_id, data)
        if not updated:
            raise HTTPException(status_code=404, detail="Saved sheet not found")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating saved_sheet %d: %s", sheet_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{sheet_id}", status_code=200)
def delete_saved_sheet(
    sheet_id: int,
    service: SavedSheetService = Depends(_get_saved_sheet_service),
) -> bool:
    """DELETE /saved-sheets/{id}."""
    try:
        deleted = service.delete(sheet_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Saved sheet not found")
        return True
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting saved_sheet %d: %s", sheet_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{sheet_id}/share", response_model=ShareResponse, status_code=201)
def share_saved_sheet(
    sheet_id: int,
    service: SavedSheetService = Depends(_get_saved_sheet_service),
) -> ShareResponse:
    """POST /saved-sheets/{id}/share — generates a UUID token + share URL."""
    try:
        result = service.generate_share(sheet_id)
        if not result:
            raise HTTPException(status_code=404, detail="Saved sheet not found")
        return ShareResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating share for saved_sheet %d: %s", sheet_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


saved_sheets_router = router  # FIX-ROUTER-ALIAS
