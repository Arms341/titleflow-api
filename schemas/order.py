"""
schemas/order.py  v1.0.0
Locked template — JARVIS title_company gig.
"""
import logging
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class OrderBase(BaseModel):
    """Shared base schema for Order."""

    saved_sheet_id: Optional[int] = None
    order_type: Optional[str] = None
    status: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_email: Optional[str] = None
    buyer_phone: Optional[str] = None
    seller_name: Optional[str] = None
    seller_email: Optional[str] = None
    seller_phone: Optional[str] = None
    lender_name: Optional[str] = None
    loan_officer_name: Optional[str] = None
    escrow_officer_preference: Optional[str] = None
    property_address: Optional[str] = None
    notes: Optional[str] = None
    contract_date: Optional[date] = None
    estimated_closing_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(OrderBase):
    """Input schema for creating an Order."""

    order_type: str = "purchase"
    seller_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrderUpdate(BaseModel):
    """Schema for updating. All fields optional."""

    order_type: Optional[str] = None
    status: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_email: Optional[str] = None
    buyer_phone: Optional[str] = None
    seller_name: Optional[str] = None
    seller_email: Optional[str] = None
    seller_phone: Optional[str] = None
    lender_name: Optional[str] = None
    loan_officer_name: Optional[str] = None
    escrow_officer_preference: Optional[str] = None
    property_address: Optional[str] = None
    notes: Optional[str] = None
    contract_date: Optional[date] = None
    estimated_closing_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    """Schema for PUT /orders/{id}/status — admin status workflow."""

    status: str

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(OrderBase):
    """Output schema."""

    id: int
    agent_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
