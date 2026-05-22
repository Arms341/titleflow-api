"""
schemas/rate_bracket.py  v1.0.0
Locked template — JARVIS title_company gig.
"""
import logging
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class RateBracketBase(BaseModel):
    """Shared base schema for RateBracket."""

    rate_table_id: Optional[int] = None
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    rate_per_thousand: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class RateBracketCreate(RateBracketBase):
    """Input schema for creating a RateBracket."""

    rate_table_id: int
    min_value: Decimal
    rate_per_thousand: Decimal

    model_config = ConfigDict(from_attributes=True)


class RateBracketUpdate(BaseModel):
    """Schema for updating RateBracket. All fields optional."""

    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    rate_per_thousand: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class RateBracketResponse(RateBracketBase):
    """Output schema for returning RateBracket."""

    id: int

    model_config = ConfigDict(from_attributes=True)


class RateBracketBulkCreate(BaseModel):
    """Bulk upload schema for POST /rate-tables/{id}/brackets."""

    brackets: List[RateBracketCreate]

    model_config = ConfigDict(from_attributes=True)
