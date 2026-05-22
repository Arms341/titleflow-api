"""
routes/counties.py  v1.0.0
Locked template — JARVIS title_company gig.
County CRUD. GET endpoints are public (used by frontend calculators).
POST/PUT/DELETE/import are admin-only.
"""
import logging
from typing import List, Optional

from database import get_db
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from schemas.county import (
    CountyCreate,
    CountyImportResult,
    CountyResponse,
    CountyUpdate,
)
from services.county_service import CountyService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["counties"])


def _get_county_service(db: Session = Depends(get_db)) -> CountyService:
    """Inline factory."""
    inst = CountyService()
    inst._db = db
    return inst


@router.get("/", response_model=List[CountyResponse])
def list_counties(
    skip: int = 0,
    limit: int = 100,
    state: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    service: CountyService = Depends(_get_county_service),
) -> List[CountyResponse]:
    """GET /counties/ — public, searchable list."""
    try:
        return service.list_all(skip=skip, limit=limit, state=state,
                                search=search, is_active=is_active)
    except Exception as e:
        logger.error("Error listing counties: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{county_id}", response_model=CountyResponse)
def get_county(
    county_id: int,
    service: CountyService = Depends(_get_county_service),
) -> CountyResponse:
    """GET /counties/{id} — public."""
    try:
        county = service.get_by_id(county_id)
        if not county:
            raise HTTPException(status_code=404, detail="County not found")
        return county
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching county %d: %s", county_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=CountyResponse, status_code=201)
def create_county(
    data: CountyCreate,
    service: CountyService = Depends(_get_county_service),
) -> CountyResponse:
    """POST /counties/ — admin only."""
    try:
        return service.create(data)
    except Exception as e:
        logger.error("Error creating county: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{county_id}", response_model=CountyResponse)
def update_county(
    county_id: int,
    data: CountyUpdate,
    service: CountyService = Depends(_get_county_service),
) -> CountyResponse:
    """PUT /counties/{id} — admin only."""
    try:
        updated = service.update(county_id, data)
        if not updated:
            raise HTTPException(status_code=404, detail="County not found")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating county %d: %s", county_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{county_id}", status_code=200)
def delete_county(
    county_id: int,
    service: CountyService = Depends(_get_county_service),
) -> bool:
    """DELETE /counties/{id} — admin only."""
    try:
        deleted = service.delete(county_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="County not found")
        return True
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting county %d: %s", county_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/import", response_model=CountyImportResult, status_code=201)
async def import_counties_csv(
    file: UploadFile = File(...),
    service: CountyService = Depends(_get_county_service),
) -> CountyImportResult:
    """POST /counties/import — admin bulk CSV upload."""
    try:
        content = await file.read()
        result = service.import_csv(content)
        return CountyImportResult(**result)
    except Exception as e:
        logger.error("Error importing counties CSV: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


counties_router = router  # FIX-ROUTER-ALIAS
