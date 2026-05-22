"""
schemas/contact.py  v1.0.0
Locked template - JARVIS title_company gig.
Pydantic schemas for Contact CRUD.
Fields: first_name, last_name, email, phone, company_name, role, notes.
"""
import logging
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class ContactBase(BaseModel):
    """Shared base fields for Contact."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    role: Optional[str] = None
    notes: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class ContactCreate(ContactBase):
    """Schema for creating a new contact."""

    first_name: str
    last_name: str
    role: str = "buyer"


class ContactUpdate(ContactBase):
    """Schema for updating an existing contact - all fields optional."""

    pass


class ContactResponse(ContactBase):
    """Schema for returning contact data in API responses."""

    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )
