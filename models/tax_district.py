"""
models/tax_district.py  v1.0.0
Tax district with combined property tax rate.
Used by calculators to auto-compute annual taxes from sale price.
Each district represents a school district area with a combined rate
(city + county + ISD + hospital + water districts rolled into one).
"""
import logging
from datetime import datetime

from models.base import Base
from sqlalchemy import Column, DateTime, Decimal, Integer, String, Boolean, ForeignKey

logger = logging.getLogger(__name__)


class TaxDistrict(Base):
    """SQLAlchemy ORM model for the tax_districts table."""

    __tablename__ = "tax_districts"

    id = Column(Integer, primary_key=True, index=True)
    county_id = Column(
        Integer,
        ForeignKey("counties.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name = Column(String(255), nullable=False)
    combined_rate_pct = Column(Decimal(6, 4), nullable=False)
    is_default = Column(Boolean, nullable=False, server_default="0")
    is_active = Column(Boolean, nullable=False, server_default="1")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<TaxDistrict id={self.id} name={self.name} rate={self.combined_rate_pct}%>"
