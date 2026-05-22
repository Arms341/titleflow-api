"""
schemas/notification.py  v1.0.0
Locked template — JARVIS title_company gig.
Pydantic schemas for Notification CRUD.
"""
import logging
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class NotificationBase(BaseModel):
    """Shared base fields for Notification."""

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class NotificationCreate(NotificationBase):
    """Schema for creating a new notification."""

    title: str
    status: str = "unread"


class NotificationUpdate(NotificationBase):
    """Schema for updating an existing notification — all fields optional."""

    pass


class NotificationResponse(NotificationBase):
    """Schema for returning notification data in API responses."""

    id: int

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )
