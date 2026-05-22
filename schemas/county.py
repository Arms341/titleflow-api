"""
schemas/county.py  v1.0.0
Locked template — JARVIS title_company gig.
County fee schedule schemas aligned with locked models/county.py.
"""
import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class CountyBase(BaseModel):
    """Shared base schema for County."""

    state: Optional[str] = None
    county_name: Optional[str] = None
    city: Optional[str] = None
    closing_fee_flat: Optional[Decimal] = None
    recording_fee_flat: Optional[Decimal] = None
    transfer_tax_rate_pct: Optional[Decimal] = None
    survey_fee_flat: Optional[Decimal] = None
    home_warranty_flat: Optional[Decimal] = None
    simultaneous_issue_discount_flat: Optional[Decimal] = None
    owner_rate_table_id: Optional[int] = None
    lender_rate_table_id: Optional[int] = None
    is_active: Optional[bool] = True
    effective_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class CountyCreate(CountyBase):
    """Input schema for creating a County."""

    state: str
    county_name: str

    model_config = ConfigDict(from_attributes=True)


class CountyUpdate(BaseModel):
    """Schema for updating a County. All fields optional."""

    state: Optional[str] = None
    county_name: Optional[str] = None
    city: Optional[str] = None
    closing_fee_flat: Optional[Decimal] = None
    recording_fee_flat: Optional[Decimal] = None
    transfer_tax_rate_pct: Optional[Decimal] = None
    survey_fee_flat: Optional[Decimal] = None
    home_warranty_flat: Optional[Decimal] = None
    simultaneous_issue_discount_flat: Optional[Decimal] = None
    owner_rate_table_id: Optional[int] = None
    lender_rate_table_id: Optional[int] = None
    is_active: Optional[bool] = None
    effective_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class CountyResponse(CountyBase):
    """Output schema for returning County."""

    id: int

    model_config = ConfigDict(from_attributes=True)


class CountyImportResult(BaseModel):
    """Result of bulk CSV import."""

    imported: int
    updated: int
    skipped: int
    errors: list = []

    model_config = ConfigDict(from_attributes=True)
