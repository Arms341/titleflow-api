"""
routes/saved_sheets.py  v1.1.0
v1.1.0: Capture agent_id from JWT on create (optional — works without auth too).
"""
import logging
from typing import List, Optional

from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query, Request
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
    inst = SavedSheetService()
    inst._db = db
    return inst


def _try_get_agent_id(request: Request, db: Session) -> Optional[int]:
    """Try to extract agent_id from JWT. Returns None if no auth or invalid."""
    try:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None
        token = auth_header.split(" ", 1)[1]
        from auth.jwt_handler import verify_token
        payload = verify_token(token)
        if not payload:
            return None
        user_id = payload.get("sub") or payload.get("user_id")
        if not user_id:
            return None
        from models.user import User
        from sqlalchemy import select
        result = db.execute(select(User).where(User.email == str(user_id)))
        user = result.scalar_one_or_none()
        if user:
            return user.id
        result = db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return user.id if user else None
    except Exception as e:
        logger.debug("Could not extract agent_id from JWT: %s", e)
        return None


@router.get("/", response_model=List[SavedSheetResponse])
def list_saved_sheets(
    skip: int = 0,
    limit: int = 100,
    sheet_type: Optional[str] = Query(None),
    service: SavedSheetService = Depends(_get_saved_sheet_service),
) -> List[SavedSheetResponse]:
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
    request: Request,
    db: Session = Depends(get_db),
    service: SavedSheetService = Depends(_get_saved_sheet_service),
) -> SavedSheetResponse:
    """POST /saved_sheets/ — captures agent_id from JWT if available."""
    try:
        agent_id = _try_get_agent_id(request, db)
        if agent_id:
            logger.info("Saving sheet with agent_id=%d", agent_id)
        return service.create(data, agent_id=agent_id)
    except Exception as e:
        logger.error("Error creating saved_sheet: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{sheet_id}", response_model=SavedSheetResponse)
def update_saved_sheet(
    sheet_id: int,
    data: SavedSheetUpdate,
    service: SavedSheetService = Depends(_get_saved_sheet_service),
) -> SavedSheetResponse:
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


saved_sheets_router = router
