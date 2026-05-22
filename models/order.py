"""
models/order.py  v1.0.0
Locked template — JARVIS title_company gig.
Title order submitted from a saved sheet. Status workflow:
submitted → opened → in_progress → closed / cancelled.
"""
import logging
from datetime import datetime

from models.base import Base
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text

logger = logging.getLogger(__name__)


class Order(Base):
    """SQLAlchemy ORM model for the orders table."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    saved_sheet_id = Column(
        Integer,
        ForeignKey("saved_sheets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    order_type = Column(String(50), nullable=False, server_default="purchase")
    status = Column(String(50), nullable=False, server_default="submitted", index=True)
    buyer_name = Column(String(255), nullable=True)
    buyer_email = Column(String(255), nullable=True)
    buyer_phone = Column(String(50), nullable=True)
    seller_name = Column(String(255), nullable=True)
    seller_email = Column(String(255), nullable=True)
    seller_phone = Column(String(50), nullable=True)
    lender_name = Column(String(255), nullable=True)
    loan_officer_name = Column(String(255), nullable=True)
    escrow_officer_preference = Column(String(255), nullable=True)
    property_address = Column(String(500), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    contract_date = Column(Date, nullable=True)
    estimated_closing_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        """Returns string representation."""
        return f"<Order id={self.id} status={self.status}>"
