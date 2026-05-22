"""
schemas/rate_table.py  v1.0.0
Locked template — JARVIS title_company gig.
Pydantic schemas aligned with locked models/rate_table.py.
"""
import logging
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class RateTableBase(BaseModel):
    """Shared base schema for RateTable."""

    name: Optional[str] = None
    state: Optional[str] = None
    county: Optional[str] = None
    table_type: Optional[str] = None
    effective_date: Optional[date] = None
    is_active: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)


class RateTableCreate(RateTableBase):
    """Input schema for creating a RateTable."""

    name: str
    state: str
    table_type: str = "owner_policy"

    model_config = ConfigDict(from_attributes=True)


class RateTableUpdate(BaseModel):
    """Schema for updating RateTable. All fields optional."""

    name: Optional[str] = None
    state: Optional[str] = None
    county: Optional[str] = None
    table_type: Optional[str] = None
    effective_date: Optional[date] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class RateTableResponse(RateTableBase):
    """Output schema for returning RateTable."""

    id: int

    model_config = ConfigDict(from_attributes=True)
