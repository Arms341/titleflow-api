"""
schemas/reissue_discount.py  v1.0.0
Locked template — JARVIS title_company gig.
"""
import logging
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class ReissueDiscountBase(BaseModel):
    """Shared base schema."""

    rate_table_id: Optional[int] = None
    years_since_prior_policy: Optional[int] = None
    discount_pct: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class ReissueDiscountCreate(ReissueDiscountBase):
    """Input schema for creating."""

    rate_table_id: int
    years_since_prior_policy: int
    discount_pct: Decimal

    model_config = ConfigDict(from_attributes=True)


class ReissueDiscountUpdate(BaseModel):
    """Schema for updating. All fields optional."""

    years_since_prior_policy: Optional[int] = None
    discount_pct: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class ReissueDiscountResponse(ReissueDiscountBase):
    """Output schema."""

    id: int

    model_config = ConfigDict(from_attributes=True)
