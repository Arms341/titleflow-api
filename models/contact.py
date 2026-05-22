"""
models/contact.py  v1.0.0
Locked template - JARVIS title_company gig.
SQLAlchemy ORM model for contacts table.
Title company contacts: buyers, sellers, agents, attorneys, lenders.
"""
import logging
from datetime import datetime

from models.base import Base
from sqlalchemy import Column, DateTime, Integer, String, Text

logger = logging.getLogger(__name__)


class Contact(Base):
    """SQLAlchemy ORM model for the contacts table."""

    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False, server_default='')
    last_name = Column(String(100), nullable=False, server_default='')
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    company_name = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, server_default='buyer')
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Contact id={self.id} name={self.first_name} {self.last_name}>"
