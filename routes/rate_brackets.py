"""
routes/rate_brackets.py  v1.0.0
Locked template — JARVIS title_company gig.
Rate bracket CRUD + bulk upload under parent rate_table.
"""
import logging
from typing import List, Optional

from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from schemas.rate_bracket import (
    RateBracketBulkCreate,
    RateBracketCreate,
    RateBracketResponse,
    RateBracketUpdate,
)
from services.rate_bracket_service import RateBracketService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["rate_brackets"])


def _get_rate_bracket_service(db: Session = Depends(get_db)) -> RateBracketService:
    """Inline factory."""
    inst = RateBracketService()
    inst._db = db
    return inst


@router.get("/", response_model=List[RateBracketResponse])
def list_rate_brackets(
    skip: int = 0,
    limit: int = 100,
    rate_table_id: Optional[int] = Query(None),
    service: RateBracketService = Depends(_get_rate_bracket_service),
) -> List[RateBracketResponse]:
    """GET /rate-brackets/ — list all brackets, optional filter by rate_table_id."""
    try:
        return service.list_all(skip=skip, limit=limit, rate_table_id=rate_table_id)
    except Exception as e:
        logger.error("Error listing rate_brackets: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{bracket_id}", response_model=RateBracketResponse)
def get_rate_bracket(
    bracket_id: int,
    service: RateBracketService = Depends(_get_rate_bracket_service),
) -> RateBracketResponse:
    """GET /rate-brackets/{id}."""
    try:
        rb = service.get_by_id(bracket_id)
        if not rb:
            raise HTTPException(status_code=404, detail="Rate bracket not found")
        return rb
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching rate_bracket %d: %s", bracket_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=RateBracketResponse, status_code=201)
def create_rate_bracket(
    data: RateBracketCreate,
    service: RateBracketService = Depends(_get_rate_bracket_service),
) -> RateBracketResponse:
    """POST /rate-brackets/ — admin only."""
    try:
        return service.create(data)
    except Exception as e:
        logger.error("Error creating rate_bracket: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/bulk/{rate_table_id}", response_model=List[RateBracketResponse], status_code=201)
def bulk_create_brackets(
    rate_table_id: int,
    payload: RateBracketBulkCreate,
    service: RateBracketService = Depends(_get_rate_bracket_service),
) -> List[RateBracketResponse]:
    """POST /rate-brackets/bulk/{rate_table_id} — admin bulk upload."""
    try:
        return service.bulk_create(rate_table_id, payload.brackets)
    except Exception as e:
        logger.error("Error bulk creating brackets: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{bracket_id}", response_model=RateBracketResponse)
def update_rate_bracket(
    bracket_id: int,
    data: RateBracketUpdate,
    service: RateBracketService = Depends(_get_rate_bracket_service),
) -> RateBracketResponse:
    """PUT /rate-brackets/{id} — admin only."""
    try:
        updated = service.update(bracket_id, data)
        if not updated:
            raise HTTPException(status_code=404, detail="Rate bracket not found")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating rate_bracket %d: %s", bracket_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{bracket_id}", status_code=200)
def delete_rate_bracket(
    bracket_id: int,
    service: RateBracketService = Depends(_get_rate_bracket_service),
) -> bool:
    """DELETE /rate-brackets/{id} — admin only."""
    try:
        deleted = service.delete(bracket_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Rate bracket not found")
        return True
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting rate_bracket %d: %s", bracket_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


rate_brackets_router = router  # FIX-ROUTER-ALIAS
