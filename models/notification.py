"""
models/notification.py  v1.0.0
Locked template — JARVIS title_company gig.
SQLAlchemy ORM model for notifications table.
"""
import logging
from datetime import datetime

from models.base import Base
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

logger = logging.getLogger(__name__)


class Notification(Base):
    """SQLAlchemy ORM model for the notifications table."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, server_default='')
    description = Column(Text, nullable=False, server_default='')
    status = Column(String(50), nullable=False, server_default='unread')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Notification id={self.id}>"
