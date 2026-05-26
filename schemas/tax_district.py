"""
schemas/tax_district.py  v1.0.0
"""
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TaxDistrictBase(BaseModel):
    name: str
    combined_rate_pct: Decimal
    county_id: Optional[int] = None
    is_default: bool = False
    is_active: bool = True
    model_config = ConfigDict(from_attributes=True)


class TaxDistrictCreate(TaxDistrictBase):
    pass


class TaxDistrictResponse(TaxDistrictBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
