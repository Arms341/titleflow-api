"""
routes/rate_tables.py  v1.0.0
Locked template — JARVIS title_company gig.
Rate table CRUD + public endpoint for calculator consumption.
Inline factory — immune to generated service factory signature bugs.
"""
import logging
from typing import List, Optional

from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from schemas.rate_table import RateTableCreate, RateTableResponse, RateTableUpdate
from services.rate_table_service import RateTableService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["rate_tables"])


def _get_rate_table_service(db: Session = Depends(get_db)) -> RateTableService:
    """Inline factory."""
    inst = RateTableService()
    inst._db = db
    return inst


@router.get("/", response_model=List[RateTableResponse])
def list_rate_tables(
    skip: int = 0,
    limit: int = 100,
    state: Optional[str] = Query(None),
    county: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    service: RateTableService = Depends(_get_rate_table_service),
) -> List[RateTableResponse]:
    """GET /rate-tables/ — list with optional filters."""
    try:
        return service.list_all(skip=skip, limit=limit, state=state,
                                county=county, is_active=is_active)
    except Exception as e:
        logger.error("Error listing rate_tables: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/public", response_model=List[RateTableResponse])
def list_public_rate_tables(
    state: str = Query(...),
    county: Optional[str] = Query(None),
    service: RateTableService = Depends(_get_rate_table_service),
) -> List[RateTableResponse]:
    """GET /rate-tables/public — unauth endpoint for calculator consumption."""
    try:
        return service.list_all(state=state, county=county, is_active=True)
    except Exception as e:
        logger.error("Error listing public rate_tables: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{rate_table_id}", response_model=RateTableResponse)
def get_rate_table(
    rate_table_id: int,
    service: RateTableService = Depends(_get_rate_table_service),
) -> RateTableResponse:
    """GET /rate-tables/{id}."""
    try:
        rt = service.get_by_id(rate_table_id)
        if not rt:
            raise HTTPException(status_code=404, detail="Rate table not found")
        return rt
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching rate_table %d: %s", rate_table_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=RateTableResponse, status_code=201)
def create_rate_table(
    data: RateTableCreate,
    service: RateTableService = Depends(_get_rate_table_service),
) -> RateTableResponse:
    """POST /rate-tables/ — admin only."""
    try:
        return service.create(data)
    except Exception as e:
        logger.error("Error creating rate_table: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{rate_table_id}", response_model=RateTableResponse)
def update_rate_table(
    rate_table_id: int,
    data: RateTableUpdate,
    service: RateTableService = Depends(_get_rate_table_service),
) -> RateTableResponse:
    """PUT /rate-tables/{id} — admin only."""
    try:
        updated = service.update(rate_table_id, data)
        if not updated:
            raise HTTPException(status_code=404, detail="Rate table not found")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating rate_table %d: %s", rate_table_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{rate_table_id}", status_code=200)
def delete_rate_table(
    rate_table_id: int,
    service: RateTableService = Depends(_get_rate_table_service),
) -> bool:
    """DELETE /rate-tables/{id} — admin only."""
    try:
        deleted = service.delete(rate_table_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Rate table not found")
        return True
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting rate_table %d: %s", rate_table_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


rate_tables_router = router  # FIX-ROUTER-ALIAS
