"""
services/contact_service.py  v1.0.0
Locked template - JARVIS title_company gig.
Contact CRUD. Uses self._db pattern (set by inline factory in route).
"""
import logging
from typing import List, Optional

from database import get_db
from fastapi import Depends
from models.contact import Contact
from schemas.contact import ContactCreate, ContactUpdate
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ContactService:
    """Business logic for contact CRUD."""

    def create_contact(self, data: ContactCreate,
                       db: Session = None) -> Contact:
        """Create a new contact."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            valid_cols = {c.name for c in Contact.__table__.columns}
            payload = {k: v for k, v in data.model_dump(exclude_none=True).items()
                       if k in valid_cols}
            payload.setdefault("role", "buyer")
            contact = Contact(**payload)
            db.add(contact)
            db.commit()
            db.refresh(contact)
            logger.info("Created contact id=%d", contact.id)
            return contact
        except Exception as e:
            db.rollback()
            logger.error("Failed to create contact: %s", e)
            raise

    def get_contact_by_id(self, id: int,
                          db: Session = None) -> Optional[Contact]:
        """Get contact by id."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            return db.get(Contact, id)
        except Exception as e:
            logger.error("Failed to get contact %d: %s", id, e)
            raise

    def list_contacts(self, skip: int = 0, limit: int = 100,
                      db: Session = None) -> List[Contact]:
        """List contacts with pagination."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            stmt = select(Contact).order_by(
                Contact.created_at.desc()
            ).offset(skip).limit(limit)
            return list(db.execute(stmt).scalars().all())
        except Exception as e:
            logger.error("Failed to list contacts: %s", e)
            raise

    def update_contact(self, id: int, data: ContactUpdate,
                       db: Session = None) -> Optional[Contact]:
        """Update an existing contact."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            contact = db.get(Contact, id)
            if not contact:
                return None
            for key, value in data.model_dump(exclude_none=True).items():
                if hasattr(contact, key):
                    setattr(contact, key, value)
            db.commit()
            db.refresh(contact)
            logger.info("Updated contact id=%d", id)
            return contact
        except Exception as e:
            db.rollback()
            logger.error("Failed to update contact %d: %s", id, e)
            raise

    def delete_contact(self, id: int,
                       db: Session = None) -> bool:
        """Delete a contact by id."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            contact = db.get(Contact, id)
            if not contact:
                return False
            db.delete(contact)
            db.commit()
            logger.info("Deleted contact id=%d", id)
            return True
        except Exception as e:
            db.rollback()
            logger.error("Failed to delete contact %d: %s", id, e)
            raise

    # --- Aliases (MPB FIX-SERVICE-METHOD-ALIAS compatible) ---
    create = create_contact
    get_by_id = get_contact_by_id
    list_all = list_contacts
    update = update_contact
    delete = delete_contact
    list = list_contacts
    get = get_contact_by_id
    get_contacts = list_contacts


def get_contact_service(db: Session = Depends(get_db)) -> ContactService:
    """FastAPI dependency - used by AI-generated routes that import this."""
    inst = ContactService()
    inst._db = db
    return inst
