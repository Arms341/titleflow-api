"""
routes/reissue_discounts.py  v1.0.0
Locked template — JARVIS title_company gig.
"""
import logging
from typing import List, Optional

from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from schemas.reissue_discount import (
    ReissueDiscountCreate,
    ReissueDiscountResponse,
    ReissueDiscountUpdate,
)
from services.reissue_discount_service import ReissueDiscountService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["reissue_discounts"])


def _get_reissue_discount_service(db: Session = Depends(get_db)) -> ReissueDiscountService:
    """Inline factory."""
    inst = ReissueDiscountService()
    inst._db = db
    return inst


@router.get("/", response_model=List[ReissueDiscountResponse])
def list_reissue_discounts(
    skip: int = 0,
    limit: int = 100,
    rate_table_id: Optional[int] = Query(None),
    service: ReissueDiscountService = Depends(_get_reissue_discount_service),
) -> List[ReissueDiscountResponse]:
    """GET /reissue-discounts/."""
    try:
        return service.list_all(skip=skip, limit=limit, rate_table_id=rate_table_id)
    except Exception as e:
        logger.error("Error listing reissue_discounts: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{discount_id}", response_model=ReissueDiscountResponse)
def get_reissue_discount(
    discount_id: int,
    service: ReissueDiscountService = Depends(_get_reissue_discount_service),
) -> ReissueDiscountResponse:
    """GET /reissue-discounts/{id}."""
    try:
        rd = service.get_by_id(discount_id)
        if not rd:
            raise HTTPException(status_code=404, detail="Reissue discount not found")
        return rd
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching reissue_discount %d: %s", discount_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=ReissueDiscountResponse, status_code=201)
def create_reissue_discount(
    data: ReissueDiscountCreate,
    service: ReissueDiscountService = Depends(_get_reissue_discount_service),
) -> ReissueDiscountResponse:
    """POST /reissue-discounts/ — admin only."""
    try:
        return service.create(data)
    except Exception as e:
        logger.error("Error creating reissue_discount: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{discount_id}", response_model=ReissueDiscountResponse)
def update_reissue_discount(
    discount_id: int,
    data: ReissueDiscountUpdate,
    service: ReissueDiscountService = Depends(_get_reissue_discount_service),
) -> ReissueDiscountResponse:
    """PUT /reissue-discounts/{id} — admin only."""
    try:
        updated = service.update(discount_id, data)
        if not updated:
            raise HTTPException(status_code=404, detail="Reissue discount not found")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating reissue_discount %d: %s", discount_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{discount_id}", status_code=200)
def delete_reissue_discount(
    discount_id: int,
    service: ReissueDiscountService = Depends(_get_reissue_discount_service),
) -> bool:
    """DELETE /reissue-discounts/{id} — admin only."""
    try:
        deleted = service.delete(discount_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Reissue discount not found")
        return True
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting reissue_discount %d: %s", discount_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


reissue_discounts_router = router  # FIX-ROUTER-ALIAS
