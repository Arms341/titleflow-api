"""
routes/tax_districts.py  v1.0.0
Tax district endpoints — public (no auth required).
Calculators need these to populate the tax district dropdown.
"""
import logging
from typing import List, Optional

from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from schemas.tax_district import TaxDistrictResponse
from services.tax_district_service import TaxDistrictService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["tax_districts"])


def _get_service(db: Session = Depends(get_db)) -> TaxDistrictService:
    inst = TaxDistrictService()
    inst._db = db
    return inst


@router.get("/", response_model=List[TaxDistrictResponse])
def list_tax_districts(
    county_id: Optional[int] = Query(None),
    service: TaxDistrictService = Depends(_get_service),
) -> List[TaxDistrictResponse]:
    """GET /tax_districts/ — list all active tax districts, optionally filtered by county."""
    try:
        return service.list_all(county_id=county_id)
    except Exception as e:
        logger.error("Error listing tax districts: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{district_id}", response_model=TaxDistrictResponse)
def get_tax_district(
    district_id: int,
    service: TaxDistrictService = Depends(_get_service),
) -> TaxDistrictResponse:
    """GET /tax_districts/{id}."""
    try:
        d = service.get_by_id(district_id)
        if not d:
            raise HTTPException(status_code=404, detail="Tax district not found")
        return d
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching tax district %d: %s", district_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
