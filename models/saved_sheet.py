"""
models/saved_sheet.py  v1.1.0
Locked template — JARVIS title_company gig.
Saved calculator output (seller net sheet OR buyer estimate).
Input + output stored as JSON for replay/share.

v1.1.0: Added client_signature (base64 PNG) and signed_at for e-signature capture.
v1.0.0: Initial model.
"""
import logging
import uuid
from datetime import datetime

from models.base import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text


logger = logging.getLogger(__name__)


def _new_share_token() -> str:
    """Generate a fresh UUID share token."""
    return uuid.uuid4().hex


class SavedSheet(Base):
    """SQLAlchemy ORM model for the saved_sheets table."""

    __tablename__ = "saved_sheets"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    sheet_type = Column(String(50), nullable=False, server_default="seller_net_sheet")
    property_address = Column(String(500), nullable=True, index=True)
    property_city = Column(String(100), nullable=True)
    client_name = Column(String(255), nullable=True)
    county_id = Column(Integer, nullable=True, index=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    share_token = Column(String(64), nullable=True, unique=True, index=True,
                         default=_new_share_token)
    is_shared = Column(Boolean, nullable=False, server_default="0")
    is_ordered = Column(Boolean, nullable=False, server_default="0")
    client_signature = Column(Text, nullable=True)
    signed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        """Returns string representation."""
        return f"<SavedSheet id={self.id} type={self.sheet_type}>"
