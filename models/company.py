"""
models/company.py  v1.1.0
Locked template — JARVIS title_company gig.
Company branding configuration. Singleton — one row enforced in service layer.

v1.1.0: Added fee_settings (JSON text) for admin-configurable fees and toggles.
"""
import logging
from datetime import datetime

from models.base import Base
from sqlalchemy import Column, DateTime, Integer, String, Text

logger = logging.getLogger(__name__)


class Company(Base):
    """SQLAlchemy ORM model for the companies table (singleton)."""

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=True, server_default="Title Company")
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(16), nullable=True, server_default="#1e3a8a")
    secondary_color = Column(String(16), nullable=True, server_default="#f59e0b")
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    address = Column(String(500), nullable=True)
    tagline = Column(String(500), nullable=True)
    disclaimer_text = Column(Text, nullable=True)
    order_submission_email = Column(String(255), nullable=True)
    fee_settings = Column(Text, nullable=True)  # JSON blob for configurable fees
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        """Returns string representation."""
        return f"<Company id={self.id} name={self.company_name}>"
