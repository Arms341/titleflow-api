"""
schemas/company.py  v1.0.0
Locked template — JARVIS title_company gig.
Singleton — no Create schema, only Update and Response.
"""
import logging
from typing import Optional

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class CompanyBase(BaseModel):
    """Shared base schema for Company."""

    company_name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    tagline: Optional[str] = None
    disclaimer_text: Optional[str] = None
    order_submission_email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CompanyCreate(CompanyBase):
    """Input schema for creating (used by service singleton-init)."""

    company_name: str

    model_config = ConfigDict(from_attributes=True)


class CompanyUpdate(CompanyBase):
    """All fields optional for PUT."""
    pass


class CompanyResponse(CompanyBase):
    """Output schema for returning Company."""

    id: int

    model_config = ConfigDict(from_attributes=True)
