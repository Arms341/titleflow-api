"""
services/notification_service.py  v1.0.0
Locked template — JARVIS title_company gig.
Notification CRUD. Uses self._db pattern (set by inline factory in route).
"""
import logging
from typing import List, Optional

from database import get_db
from fastapi import Depends
from models.notification import Notification
from schemas.notification import NotificationCreate, NotificationUpdate
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class NotificationService:
    """Business logic for notification CRUD."""

    def create_notification(self, data: NotificationCreate,
                            db: Session = None) -> Notification:
        """Create a new notification."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            valid_cols = {c.name for c in Notification.__table__.columns}
            payload = {k: v for k, v in data.model_dump(exclude_none=True).items()
                       if k in valid_cols}
            payload.setdefault("status", "unread")
            notification = Notification(**payload)
            db.add(notification)
            db.commit()
            db.refresh(notification)
            logger.info("Created notification id=%d", notification.id)
            return notification
        except Exception as e:
            db.rollback()
            logger.error("Failed to create notification: %s", e)
            raise

    def get_notification_by_id(self, id: int,
                                db: Session = None) -> Optional[Notification]:
        """Get notification by id."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            return db.get(Notification, id)
        except Exception as e:
            logger.error("Failed to get notification %d: %s", id, e)
            raise

    def list_notifications(self, skip: int = 0, limit: int = 100,
                           db: Session = None) -> List[Notification]:
        """List notifications with pagination."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            stmt = select(Notification).order_by(
                Notification.created_at.desc()
            ).offset(skip).limit(limit)
            return list(db.execute(stmt).scalars().all())
        except Exception as e:
            logger.error("Failed to list notifications: %s", e)
            raise

    def update_notification(self, id: int, data: NotificationUpdate,
                            db: Session = None) -> Optional[Notification]:
        """Update an existing notification."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            notification = db.get(Notification, id)
            if not notification:
                return None
            for key, value in data.model_dump(exclude_none=True).items():
                if hasattr(notification, key):
                    setattr(notification, key, value)
            db.commit()
            db.refresh(notification)
            logger.info("Updated notification id=%d", id)
            return notification
        except Exception as e:
            db.rollback()
            logger.error("Failed to update notification %d: %s", id, e)
            raise

    def delete_notification(self, id: int,
                            db: Session = None) -> bool:
        """Delete a notification by id."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            notification = db.get(Notification, id)
            if not notification:
                return False
            db.delete(notification)
            db.commit()
            logger.info("Deleted notification id=%d", id)
            return True
        except Exception as e:
            db.rollback()
            logger.error("Failed to delete notification %d: %s", id, e)
            raise

    # --- Aliases (MPB FIX-SERVICE-METHOD-ALIAS compatible) ---
    create = create_notification
    get_by_id = get_notification_by_id
    list_all = list_notifications
    update = update_notification
    delete = delete_notification
    list = list_notifications
    get = get_notification_by_id


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    """FastAPI dependency — used by AI-generated routes that import this."""
    inst = NotificationService()
    inst._db = db
    return inst
