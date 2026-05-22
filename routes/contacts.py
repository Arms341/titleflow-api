"""
routes/contacts.py  v1.0.0
Locked template - JARVIS title_company gig.
Contact CRUD. Fields: first_name, last_name, email, phone, company_name, role, notes.
Standard REST: GET /, GET /{id}, POST /, PUT /{id}, DELETE /{id}.
"""
import logging
from typing import List

from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from schemas.contact import (
    ContactCreate,
    ContactResponse,
    ContactUpdate,
)
from services.contact_service import ContactService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["contacts"])


def _get_contact_service(db: Session = Depends(get_db)) -> ContactService:
    """Inline factory."""
    inst = ContactService()
    inst._db = db
    return inst


@router.get("/", response_model=List[ContactResponse])
def list_contacts(
    skip: int = 0,
    limit: int = 100,
    service: ContactService = Depends(_get_contact_service),
) -> List[ContactResponse]:
    """GET /contacts/."""
    try:
        return service.list_all(skip=skip, limit=limit)
    except Exception as e:
        logger.error("Error listing contacts: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(
    contact_id: int,
    service: ContactService = Depends(_get_contact_service),
) -> ContactResponse:
    """GET /contacts/{id}."""
    try:
        contact = service.get_by_id(contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        return contact
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching contact %d: %s", contact_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=ContactResponse, status_code=201)
def create_contact(
    data: ContactCreate,
    service: ContactService = Depends(_get_contact_service),
) -> ContactResponse:
    """POST /contacts/ - create a new contact."""
    try:
        return service.create(data)
    except Exception as e:
        logger.error("Error creating contact: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: int,
    data: ContactUpdate,
    service: ContactService = Depends(_get_contact_service),
) -> ContactResponse:
    """PUT /contacts/{id}."""
    try:
        updated = service.update(contact_id, data)
        if not updated:
            raise HTTPException(status_code=404, detail="Contact not found")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating contact %d: %s", contact_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{contact_id}", status_code=200)
def delete_contact(
    contact_id: int,
    service: ContactService = Depends(_get_contact_service),
) -> bool:
    """DELETE /contacts/{id}."""
    try:
        deleted = service.delete(contact_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Contact not found")
        return True
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting contact %d: %s", contact_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


contacts_router = router  # FIX-ROUTER-ALIAS
