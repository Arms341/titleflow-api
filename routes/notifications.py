"""
routes/notifications.py  v1.0.0
Locked template — JARVIS title_company gig.
Notification CRUD. Fields: title, description, status.
FORBIDDEN field names: message, content, body, text, type, subject.
"""
import logging
from typing import List

from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
)
from services.notification_service import NotificationService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["notifications"])


def _get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    """Inline factory."""
    inst = NotificationService()
    inst._db = db
    return inst


@router.get("/", response_model=List[NotificationResponse])
def list_notifications(
    skip: int = 0,
    limit: int = 100,
    service: NotificationService = Depends(_get_notification_service),
) -> List[NotificationResponse]:
    """GET /notifications/."""
    try:
        return service.list_all(skip=skip, limit=limit)
    except Exception as e:
        logger.error("Error listing notifications: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification(
    notification_id: int,
    service: NotificationService = Depends(_get_notification_service),
) -> NotificationResponse:
    """GET /notifications/{id}."""
    try:
        notification = service.get_by_id(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching notification %d: %s", notification_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=NotificationResponse, status_code=201)
def create_notification(
    data: NotificationCreate,
    service: NotificationService = Depends(_get_notification_service),
) -> NotificationResponse:
    """POST /notifications/ — create a new notification."""
    try:
        return service.create(data)
    except Exception as e:
        logger.error("Error creating notification: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{notification_id}", response_model=NotificationResponse)
def update_notification(
    notification_id: int,
    data: NotificationUpdate,
    service: NotificationService = Depends(_get_notification_service),
) -> NotificationResponse:
    """PUT /notifications/{id}."""
    try:
        updated = service.update(notification_id, data)
        if not updated:
            raise HTTPException(status_code=404, detail="Notification not found")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating notification %d: %s", notification_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{notification_id}", status_code=200)
def delete_notification(
    notification_id: int,
    service: NotificationService = Depends(_get_notification_service),
) -> bool:
    """DELETE /notifications/{id}."""
    try:
        deleted = service.delete(notification_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Notification not found")
        return True
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting notification %d: %s", notification_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


notifications_router = router  # FIX-ROUTER-ALIAS
