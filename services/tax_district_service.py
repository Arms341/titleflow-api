"""
services/tax_district_service.py  v1.0.0
Tax district CRUD — list by county, get by ID.
"""
import logging
from typing import List, Optional

from models.tax_district import TaxDistrict
from schemas.tax_district import TaxDistrictCreate
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Service-layer error."""
    pass


class TaxDistrictService:
    """Tax district service."""

    _db: Session = None

    def list_all(self, county_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[TaxDistrict]:
        q = select(TaxDistrict).where(TaxDistrict.is_active == True)
        if county_id:
            q = q.where(TaxDistrict.county_id == county_id)
        q = q.order_by(TaxDistrict.name).offset(skip).limit(limit)
        return list(self._db.execute(q).scalars().all())

    def get_by_id(self, id: int) -> Optional[TaxDistrict]:
        result = self._db.execute(select(TaxDistrict).where(TaxDistrict.id == id))
        return result.scalar_one_or_none()

    def create(self, data: TaxDistrictCreate) -> TaxDistrict:
        obj = TaxDistrict(**data.model_dump())
        self._db.add(obj)
        self._db.commit()
        self._db.refresh(obj)
        return obj
