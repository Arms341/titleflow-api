"""
services/reissue_discount_service.py  v1.0.0
Locked template — JARVIS title_company gig.
ReissueDiscount CRUD.
"""
import logging
from typing import List, Optional

from database import get_db
from fastapi import Depends
from models.reissue_discount import ReissueDiscount
from schemas.reissue_discount import ReissueDiscountCreate, ReissueDiscountUpdate
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Service-layer error."""
    pass


class ReissueDiscountService:
    """Business logic for reissue_discount CRUD."""

    def create_reissue_discount(self, data: ReissueDiscountCreate, db: Session = None) -> ReissueDiscount:
        """Create a new reissue discount row."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            valid_cols = {c.name for c in ReissueDiscount.__table__.columns}
            rd = ReissueDiscount(**{
                k: v for k, v in data.model_dump(exclude_none=True).items()
                if k in valid_cols
            })
            db.add(rd)
            db.commit()
            db.refresh(rd)
            logger.info("Created reissue_discount id=%d", rd.id)
            return rd
        except Exception as e:
            db.rollback()
            logger.error("Failed to create reissue_discount: %s", e)
            raise ServiceError(f"Failed to create reissue_discount: {e}") from e

    def get_reissue_discount_by_id(self, id: int, db: Session = None) -> Optional[ReissueDiscount]:
        """Get by id."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            return db.get(ReissueDiscount, id)
        except Exception as e:
            logger.error("Failed to get reissue_discount %d: %s", id, e)
            raise ServiceError(f"Failed to get reissue_discount: {e}") from e

    def list_reissue_discounts(self, skip: int = 0, limit: int = 100,
                               rate_table_id: Optional[int] = None,
                               db: Session = None) -> List[ReissueDiscount]:
        """List reissue discounts, optionally filtered."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            stmt = select(ReissueDiscount)
            if rate_table_id is not None:
                stmt = stmt.where(ReissueDiscount.rate_table_id == rate_table_id)
            stmt = stmt.order_by(ReissueDiscount.years_since_prior_policy.asc()).offset(skip).limit(limit)
            return list(db.execute(stmt).scalars().all())
        except Exception as e:
            logger.error("Failed to list reissue_discounts: %s", e)
            raise ServiceError(f"Failed to list reissue_discounts: {e}") from e

    def update_reissue_discount(self, id: int, data: ReissueDiscountUpdate,
                                db: Session = None) -> Optional[ReissueDiscount]:
        """Update existing."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            rd = db.get(ReissueDiscount, id)
            if not rd:
                return None
            for key, value in data.model_dump(exclude_unset=True).items():
                if hasattr(rd, key):
                    setattr(rd, key, value)
            db.commit()
            db.refresh(rd)
            logger.info("Updated reissue_discount id=%d", id)
            return rd
        except Exception as e:
            db.rollback()
            logger.error("Failed to update reissue_discount %d: %s", id, e)
            raise ServiceError(f"Failed to update reissue_discount: {e}") from e

    def delete_reissue_discount(self, id: int, db: Session = None) -> bool:
        """Delete."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            rd = db.get(ReissueDiscount, id)
            if not rd:
                return False
            db.delete(rd)
            db.commit()
            logger.info("Deleted reissue_discount id=%d", id)
            return True
        except Exception as e:
            db.rollback()
            logger.error("Failed to delete reissue_discount %d: %s", id, e)
            raise ServiceError(f"Failed to delete reissue_discount: {e}") from e

    # Aliases
    create = create_reissue_discount
    get_by_id = get_reissue_discount_by_id
    list_all = list_reissue_discounts
    list = list_reissue_discounts
    get_all = list_reissue_discounts
    update = update_reissue_discount
    delete = delete_reissue_discount
    get = get_reissue_discount_by_id


def get_reissue_discount_service(db: Session = Depends(get_db)) -> ReissueDiscountService:
    """FastAPI dependency."""
    inst = ReissueDiscountService()
    inst._db = db
    return inst
