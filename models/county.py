"""
models/county.py  v1.0.0
Locked template — JARVIS title_company gig.
County fee schedule with FKs to owner and lender rate tables.
"""
import logging
from datetime import datetime

from models.base import Base
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String

logger = logging.getLogger(__name__)


class County(Base):
    """SQLAlchemy ORM model for the counties table."""

    __tablename__ = "counties"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(2), nullable=False, index=True)
    county_name = Column(String(100), nullable=False, index=True)
    city = Column(String(100), nullable=True, index=True)
    closing_fee_flat = Column(Numeric(10, 2), nullable=True, default=0)
    recording_fee_flat = Column(Numeric(10, 2), nullable=True, default=0)
    transfer_tax_rate_pct = Column(Numeric(6, 4), nullable=True, default=0)
    survey_fee_flat = Column(Numeric(10, 2), nullable=True, default=0)
    home_warranty_flat = Column(Numeric(10, 2), nullable=True, default=0)
    simultaneous_issue_discount_flat = Column(Numeric(10, 2), nullable=True, default=0)
    owner_rate_table_id = Column(
        Integer,
        ForeignKey("rate_tables.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    lender_rate_table_id = Column(
        Integer,
        ForeignKey("rate_tables.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active = Column(Boolean, nullable=False, server_default="1")
    effective_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        """Returns string representation."""
        return f"<County id={self.id} {self.state}/{self.county_name}>"
