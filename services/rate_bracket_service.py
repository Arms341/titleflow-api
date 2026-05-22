"""
services/rate_bracket_service.py  v1.0.0
Locked template — JARVIS title_company gig.
RateBracket CRUD + bulk_create for POST /rate-tables/{id}/brackets.
"""
import logging
from typing import List, Optional

from database import get_db
from fastapi import Depends
from models.rate_bracket import RateBracket
from schemas.rate_bracket import RateBracketCreate, RateBracketUpdate
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Service-layer error."""
    pass


class RateBracketService:
    """Business logic for rate_bracket CRUD."""

    def create_rate_bracket(self, data: RateBracketCreate, db: Session = None) -> RateBracket:
        """Create a new rate bracket."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            valid_cols = {c.name for c in RateBracket.__table__.columns}
            rb = RateBracket(**{
                k: v for k, v in data.model_dump(exclude_none=True).items()
                if k in valid_cols
            })
            db.add(rb)
            db.commit()
            db.refresh(rb)
            logger.info("Created rate_bracket id=%d", rb.id)
            return rb
        except Exception as e:
            db.rollback()
            logger.error("Failed to create rate_bracket: %s", e)
            raise ServiceError(f"Failed to create rate_bracket: {e}") from e

    def bulk_create(self, rate_table_id: int, brackets: List[RateBracketCreate],
                    db: Session = None) -> List[RateBracket]:
        """Bulk-create brackets under a rate_table_id."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            valid_cols = {c.name for c in RateBracket.__table__.columns}
            created = []
            for b in brackets:
                payload = {k: v for k, v in b.model_dump(exclude_none=True).items()
                           if k in valid_cols}
                payload["rate_table_id"] = rate_table_id
                rb = RateBracket(**payload)
                db.add(rb)
                created.append(rb)
            db.commit()
            for rb in created:
                db.refresh(rb)
            logger.info("Bulk-created %d brackets for rate_table_id=%d",
                        len(created), rate_table_id)
            return created
        except Exception as e:
            db.rollback()
            logger.error("Failed to bulk create brackets: %s", e)
            raise ServiceError(f"Failed to bulk create brackets: {e}") from e

    def get_rate_bracket_by_id(self, id: int, db: Session = None) -> Optional[RateBracket]:
        """Get bracket by id."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            return db.get(RateBracket, id)
        except Exception as e:
            logger.error("Failed to get rate_bracket %d: %s", id, e)
            raise ServiceError(f"Failed to get rate_bracket: {e}") from e

    def list_rate_brackets(self, skip: int = 0, limit: int = 100,
                           rate_table_id: Optional[int] = None,
                           db: Session = None) -> List[RateBracket]:
        """List brackets, optionally filtered by rate_table_id."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            stmt = select(RateBracket)
            if rate_table_id is not None:
                stmt = stmt.where(RateBracket.rate_table_id == rate_table_id)
            stmt = stmt.order_by(RateBracket.min_value.asc()).offset(skip).limit(limit)
            return list(db.execute(stmt).scalars().all())
        except Exception as e:
            logger.error("Failed to list rate_brackets: %s", e)
            raise ServiceError(f"Failed to list rate_brackets: {e}") from e

    def update_rate_bracket(self, id: int, data: RateBracketUpdate,
                            db: Session = None) -> Optional[RateBracket]:
        """Update an existing bracket."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            rb = db.get(RateBracket, id)
            if not rb:
                return None
            for key, value in data.model_dump(exclude_unset=True).items():
                if hasattr(rb, key):
                    setattr(rb, key, value)
            db.commit()
            db.refresh(rb)
            logger.info("Updated rate_bracket id=%d", id)
            return rb
        except Exception as e:
            db.rollback()
            logger.error("Failed to update rate_bracket %d: %s", id, e)
            raise ServiceError(f"Failed to update rate_bracket: {e}") from e

    def delete_rate_bracket(self, id: int, db: Session = None) -> bool:
        """Delete a bracket."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            rb = db.get(RateBracket, id)
            if not rb:
                return False
            db.delete(rb)
            db.commit()
            logger.info("Deleted rate_bracket id=%d", id)
            return True
        except Exception as e:
            db.rollback()
            logger.error("Failed to delete rate_bracket %d: %s", id, e)
            raise ServiceError(f"Failed to delete rate_bracket: {e}") from e

    # Aliases
    create = create_rate_bracket
    get_by_id = get_rate_bracket_by_id
    list_all = list_rate_brackets
    list = list_rate_brackets
    get_all = list_rate_brackets
    update = update_rate_bracket
    delete = delete_rate_bracket
    get = get_rate_bracket_by_id


def get_rate_bracket_service(db: Session = Depends(get_db)) -> RateBracketService:
    """FastAPI dependency."""
    inst = RateBracketService()
    inst._db = db
    return inst
