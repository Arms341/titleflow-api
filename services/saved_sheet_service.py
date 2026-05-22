"""
services/saved_sheet_service.py  v1.0.0
Locked template — JARVIS title_company gig.
SavedSheet CRUD + share token rotation + public lookup by token.
"""
import logging
import os
import uuid
from typing import List, Optional

from database import get_db
from fastapi import Depends
from models.saved_sheet import SavedSheet
from schemas.saved_sheet import SavedSheetCreate, SavedSheetUpdate
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Service-layer error."""
    pass


class SavedSheetService:
    """Business logic for saved_sheet CRUD + sharing."""

    def create_saved_sheet(self, data: SavedSheetCreate, agent_id: Optional[int] = None,
                           db: Session = None) -> SavedSheet:
        """Create a new saved sheet."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            valid_cols = {c.name for c in SavedSheet.__table__.columns}
            payload = {k: v for k, v in data.model_dump(exclude_none=True).items()
                       if k in valid_cols}
            if agent_id is not None:
                payload["agent_id"] = agent_id
            if "share_token" not in payload:
                payload["share_token"] = uuid.uuid4().hex
            sheet = SavedSheet(**payload)
            db.add(sheet)
            db.commit()
            db.refresh(sheet)
            logger.info("Created saved_sheet id=%d", sheet.id)
            return sheet
        except Exception as e:
            db.rollback()
            logger.error("Failed to create saved_sheet: %s", e)
            raise ServiceError(f"Failed to create saved_sheet: {e}") from e

    def get_saved_sheet_by_id(self, id: int, db: Session = None) -> Optional[SavedSheet]:
        """Get saved sheet by id."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            return db.get(SavedSheet, id)
        except Exception as e:
            logger.error("Failed to get saved_sheet %d: %s", id, e)
            raise ServiceError(f"Failed to get saved_sheet: {e}") from e

    def get_by_share_token(self, token: str, db: Session = None) -> Optional[SavedSheet]:
        """Public lookup used by GET /shared/{token}."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            stmt = select(SavedSheet).where(SavedSheet.share_token == token)
            return db.execute(stmt).scalars().first()
        except Exception as e:
            logger.error("Failed to lookup share_token: %s", e)
            raise ServiceError(f"Failed to lookup share_token: {e}") from e

    def list_saved_sheets(self, skip: int = 0, limit: int = 100,
                          agent_id: Optional[int] = None,
                          sheet_type: Optional[str] = None,
                          db: Session = None) -> List[SavedSheet]:
        """List saved sheets, optionally filtered by agent + type."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            stmt = select(SavedSheet)
            if agent_id is not None:
                stmt = stmt.where(SavedSheet.agent_id == agent_id)
            if sheet_type is not None:
                stmt = stmt.where(SavedSheet.sheet_type == sheet_type)
            stmt = stmt.order_by(SavedSheet.created_at.desc()).offset(skip).limit(limit)
            return list(db.execute(stmt).scalars().all())
        except Exception as e:
            logger.error("Failed to list saved_sheets: %s", e)
            raise ServiceError(f"Failed to list saved_sheets: {e}") from e

    def update_saved_sheet(self, id: int, data: SavedSheetUpdate,
                           db: Session = None) -> Optional[SavedSheet]:
        """Update an existing saved sheet."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            sheet = db.get(SavedSheet, id)
            if not sheet:
                return None
            for key, value in data.model_dump(exclude_unset=True).items():
                if hasattr(sheet, key):
                    setattr(sheet, key, value)
            db.commit()
            db.refresh(sheet)
            logger.info("Updated saved_sheet id=%d", id)
            return sheet
        except Exception as e:
            db.rollback()
            logger.error("Failed to update saved_sheet %d: %s", id, e)
            raise ServiceError(f"Failed to update saved_sheet: {e}") from e

    def delete_saved_sheet(self, id: int, db: Session = None) -> bool:
        """Delete a saved sheet."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            sheet = db.get(SavedSheet, id)
            if not sheet:
                return False
            db.delete(sheet)
            db.commit()
            logger.info("Deleted saved_sheet id=%d", id)
            return True
        except Exception as e:
            db.rollback()
            logger.error("Failed to delete saved_sheet %d: %s", id, e)
            raise ServiceError(f"Failed to delete saved_sheet: {e}") from e

    def generate_share(self, id: int, db: Session = None) -> Optional[dict]:
        """Rotate share_token + mark is_shared=True. Returns dict with token + url."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            sheet = db.get(SavedSheet, id)
            if not sheet:
                return None
            sheet.share_token = uuid.uuid4().hex
            sheet.is_shared = True
            db.commit()
            db.refresh(sheet)
            base_url = os.environ.get("BASE_URL", "http://localhost:8000")
            return {
                "share_token": sheet.share_token,
                "share_url": f"{base_url}/shared/{sheet.share_token}",
            }
        except Exception as e:
            db.rollback()
            logger.error("Failed to generate share for saved_sheet %d: %s", id, e)
            raise ServiceError(f"Failed to generate share: {e}") from e

    # Aliases
    create = create_saved_sheet
    get_by_id = get_saved_sheet_by_id
    list_all = list_saved_sheets
    list = list_saved_sheets
    get_all = list_saved_sheets
    update = update_saved_sheet
    delete = delete_saved_sheet
    get = get_saved_sheet_by_id


def get_saved_sheet_service(db: Session = Depends(get_db)) -> SavedSheetService:
    """FastAPI dependency."""
    inst = SavedSheetService()
    inst._db = db
    return inst
