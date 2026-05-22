"""
schemas/saved_sheet.py  v1.0.0
Locked template — JARVIS title_company gig.
"""
import logging
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class SavedSheetBase(BaseModel):
    """Shared base schema for SavedSheet."""

    sheet_type: Optional[str] = None
    property_address: Optional[str] = None
    property_city: Optional[str] = None
    client_name: Optional[str] = None
    county_id: Optional[int] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    is_shared: Optional[bool] = False
    is_ordered: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)


class SavedSheetCreate(SavedSheetBase):
    """Input schema for creating a SavedSheet."""

    sheet_type: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class SavedSheetUpdate(BaseModel):
    """Schema for updating. All fields optional."""

    property_address: Optional[str] = None
    property_city: Optional[str] = None
    client_name: Optional[str] = None
    is_shared: Optional[bool] = None
    is_ordered: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class SavedSheetResponse(SavedSheetBase):
    """Output schema."""

    id: int
    agent_id: Optional[int] = None
    share_token: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ShareResponse(BaseModel):
    """Response from POST /saved-sheets/{id}/share."""

    share_token: str
    share_url: str

    model_config = ConfigDict(from_attributes=True)
