"""
models/reissue_discount.py  v1.0.0
Locked template — JARVIS title_company gig.
Reissue rate discount row. Child of rate_tables. Matched by
years_since_prior_policy bracket (e.g. <=5 years → 30% discount).
"""
import logging
from datetime import datetime

from models.base import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric

logger = logging.getLogger(__name__)


class ReissueDiscount(Base):
    """SQLAlchemy ORM model for the reissue_discounts table."""

    __tablename__ = "reissue_discounts"

    id = Column(Integer, primary_key=True, index=True)
    rate_table_id = Column(
        Integer,
        ForeignKey("rate_tables.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    years_since_prior_policy = Column(Integer, nullable=False, default=5)
    discount_pct = Column(Numeric(5, 2), nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        """Returns string representation."""
        return f"<ReissueDiscount id={self.id} rate_table_id={self.rate_table_id}>"
