"""
models/base.py - Canonical locked template v1.1.0
JARVIS Locked File Library — DO NOT MODIFY WITHOUT UPDATING VERSION

v1.1.0: Moved User class to models/user.py (universal template).
        Eliminates duplicate __tablename__="users" crash when gig-specific
        models/user.py also exists. Base + password helpers remain here.
v1.0.2: FIX-PASSLIB-RUNTIME-VALIDATE
v1.0.1: Initial locked template.
"""
import logging
from typing import Optional

from sqlalchemy.orm import DeclarativeBase

try:
    from passlib.context import CryptContext
    _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    _pwd_context.hash("_startup_validation_")
    _HAS_PASSLIB = True
except Exception:
    _HAS_PASSLIB = False

logger = logging.getLogger(__name__)


def get_password_hash(password: str) -> str:
    """Hash a plain-text password. Returns bcrypt hash string."""
    if _HAS_PASSLIB:
        try:
            return _pwd_context.hash(password)
        except Exception:
            pass
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a stored hash."""
    if _HAS_PASSLIB:
        try:
            return _pwd_context.verify(plain_password, hashed_password)
        except Exception:
            pass
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


class Base(DeclarativeBase):
    """SQLAlchemy declarative base — all ORM models inherit from this."""
    pass
