"""
services/rate_table_service.py  v1.0.0
Locked template — JARVIS title_company gig.
RateTable CRUD + critical bracket math function get_title_premium().
This is the core pricing engine — must never be AI-generated.
"""
import logging
from decimal import Decimal
from typing import List, Optional

from database import get_db
from fastapi import Depends
from models.rate_bracket import RateBracket
from models.rate_table import RateTable
from models.reissue_discount import ReissueDiscount
from schemas.rate_table import RateTableCreate, RateTableUpdate
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Service-layer error."""
    pass


class RateTableService:
    """Business logic for rate_table CRUD + title premium bracket math."""

    def create_rate_table(self, data: RateTableCreate, db: Session = None) -> RateTable:
        """Create a new rate table."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            valid_cols = {c.name for c in RateTable.__table__.columns}
            rt = RateTable(**{
                k: v for k, v in data.model_dump(exclude_none=True).items()
                if k in valid_cols
            })
            db.add(rt)
            db.commit()
            db.refresh(rt)
            logger.info("Created rate_table id=%d", rt.id)
            return rt
        except Exception as e:
            db.rollback()
            logger.error("Failed to create rate_table: %s", e)
            raise ServiceError(f"Failed to create rate_table: {e}") from e

    def get_rate_table_by_id(self, id: int, db: Session = None) -> Optional[RateTable]:
        """Get rate table by id."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            return db.get(RateTable, id)
        except Exception as e:
            logger.error("Failed to get rate_table %d: %s", id, e)
            raise ServiceError(f"Failed to get rate_table: {e}") from e

    def list_rate_tables(self, skip: int = 0, limit: int = 100,
                         state: Optional[str] = None, county: Optional[str] = None,
                         is_active: Optional[bool] = None,
                         db: Session = None) -> List[RateTable]:
        """List rate tables with optional filters."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            stmt = select(RateTable)
            if state is not None:
                stmt = stmt.where(RateTable.state == state)
            if county is not None:
                stmt = stmt.where(RateTable.county == county)
            if is_active is not None:
                stmt = stmt.where(RateTable.is_active == is_active)
            stmt = stmt.offset(skip).limit(limit)
            return list(db.execute(stmt).scalars().all())
        except Exception as e:
            logger.error("Failed to list rate_tables: %s", e)
            raise ServiceError(f"Failed to list rate_tables: {e}") from e

    def update_rate_table(self, id: int, data: RateTableUpdate, db: Session = None) -> Optional[RateTable]:
        """Update an existing rate table."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            rt = db.get(RateTable, id)
            if not rt:
                return None
            for key, value in data.model_dump(exclude_unset=True).items():
                if hasattr(rt, key):
                    setattr(rt, key, value)
            db.commit()
            db.refresh(rt)
            logger.info("Updated rate_table id=%d", id)
            return rt
        except Exception as e:
            db.rollback()
            logger.error("Failed to update rate_table %d: %s", id, e)
            raise ServiceError(f"Failed to update rate_table: {e}") from e

    def delete_rate_table(self, id: int, db: Session = None) -> bool:
        """Delete a rate table."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            rt = db.get(RateTable, id)
            if not rt:
                return False
            db.delete(rt)
            db.commit()
            logger.info("Deleted rate_table id=%d", id)
            return True
        except Exception as e:
            db.rollback()
            logger.error("Failed to delete rate_table %d: %s", id, e)
            raise ServiceError(f"Failed to delete rate_table: {e}") from e

    def get_title_premium(self, sale_price: Decimal, rate_table_id: int,
                          db: Session = None) -> Decimal:
        """
        CRITICAL BUSINESS LOGIC — DO NOT MODIFY.
        Calculate title insurance premium using tiered bracket pricing.

        For each bracket where min_value < sale_price:
            bracket_price = (min(max_value, sale_price) - min_value) *
                            rate_per_thousand / 1000

        Returns sum of all bracket prices. Uses Decimal throughout.
        """
        db = db if db is not None else getattr(self, "_db", None)
        try:
            sale_price = Decimal(str(sale_price))
            stmt = select(RateBracket).where(
                RateBracket.rate_table_id == rate_table_id
            ).order_by(RateBracket.min_value.asc())
            brackets = list(db.execute(stmt).scalars().all())

            if not brackets:
                logger.warning("No brackets found for rate_table_id=%d", rate_table_id)
                return Decimal("0.00")

            total = Decimal("0.00")
            for bracket in brackets:
                min_val = Decimal(str(bracket.min_value))
                if min_val >= sale_price:
                    break
                max_val = Decimal(str(bracket.max_value)) if bracket.max_value else sale_price
                rate = Decimal(str(bracket.rate_per_thousand))
                effective_max = sale_price if sale_price < max_val else max_val
                bracket_amount = (effective_max - min_val) * rate / Decimal("1000")
                total += bracket_amount

            quantized = total.quantize(Decimal("0.01"))
            logger.info("Title premium for %s on rate_table %d = %s",
                        sale_price, rate_table_id, quantized)
            return quantized
        except Exception as e:
            logger.error("Failed to calculate title premium: %s", e)
            raise ServiceError(f"Failed to calculate title premium: {e}") from e

    def get_reissue_discount(self, base_premium: Decimal, years_since_prior: int,
                             rate_table_id: int, db: Session = None) -> Decimal:
        """
        Calculate reissue discount on base title premium.
        Looks up ReissueDiscount row where years_since_prior_policy >= years_since_prior.
        Returns discount amount (always >= 0).
        """
        db = db if db is not None else getattr(self, "_db", None)
        try:
            base_premium = Decimal(str(base_premium))
            stmt = select(ReissueDiscount).where(
                ReissueDiscount.rate_table_id == rate_table_id,
                ReissueDiscount.years_since_prior_policy >= years_since_prior,
            ).order_by(ReissueDiscount.years_since_prior_policy.asc())
            discount_row = db.execute(stmt).scalars().first()

            if not discount_row:
                return Decimal("0.00")

            discount_pct = Decimal(str(discount_row.discount_pct))
            discount_amount = (base_premium * discount_pct / Decimal("100")).quantize(Decimal("0.01"))
            return discount_amount
        except Exception as e:
            logger.error("Failed to calculate reissue discount: %s", e)
            return Decimal("0.00")

    # Aliases
    create = create_rate_table
    get_by_id = get_rate_table_by_id
    list_all = list_rate_tables
    list = list_rate_tables
    get_all = list_rate_tables
    update = update_rate_table
    delete = delete_rate_table
    get = get_rate_table_by_id


def get_rate_table_service(db: Session = Depends(get_db)) -> RateTableService:
    """FastAPI dependency: returns RateTableService with db injected."""
    inst = RateTableService()
    inst._db = db
    return inst
