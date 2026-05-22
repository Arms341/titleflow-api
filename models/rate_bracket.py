"""
models/rate_bracket.py  v1.0.0
Locked template — JARVIS title_company gig.
Title insurance bracket row. Child of rate_tables.
"""
import logging
from datetime import datetime

from models.base import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric

logger = logging.getLogger(__name__)


class RateBracket(Base):
    """SQLAlchemy ORM model for the rate_brackets table."""

    __tablename__ = "rate_brackets"

    id = Column(Integer, primary_key=True, index=True)
    rate_table_id = Column(
        Integer,
        ForeignKey("rate_tables.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    min_value = Column(Numeric(14, 2), nullable=False, default=0)
    max_value = Column(Numeric(14, 2), nullable=True)
    rate_per_thousand = Column(Numeric(8, 4), nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        """Returns string representation."""
        return f"<RateBracket id={self.id} rate_table_id={self.rate_table_id}>"
