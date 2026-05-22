"""
models/rate_table.py  v1.0.0
Locked template — JARVIS title_company gig.
Title insurance rate table. One table per (state, county, table_type) tuple.
Brackets are children (see models/rate_bracket.py).
"""
import logging
from datetime import datetime

from models.base import Base
from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String

logger = logging.getLogger(__name__)


class RateTable(Base):
    """SQLAlchemy ORM model for the rate_tables table."""

    __tablename__ = "rate_tables"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    state = Column(String(2), nullable=False, index=True)
    county = Column(String(100), nullable=True, index=True)
    table_type = Column(String(50), nullable=False, server_default="owner_policy")
    effective_date = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="1")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        """Returns string representation of the RateTable instance."""
        return f"<RateTable id={self.id} name={self.name}>"
