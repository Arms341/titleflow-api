"""
schemas/base.py - Canonical locked template v1.0.0
JARVIS Locked File Library

Rules:
1. Pydantic schemas ONLY — zero SQLAlchemy, zero ORM imports
2. AppBaseModel is a Pydantic BaseModel — NOT an SQLAlchemy ORM base
3. No class named anything that could be mistaken for an ORM model
4. No JWT logic — that belongs in auth/jwt_handler.py
"""
import logging
from typing import Optional, Any, Dict

from pydantic import BaseModel

try:
    from pydantic import ConfigDict
    _HAS_CONFIG_DICT = True
except ImportError:
    _HAS_CONFIG_DICT = False

logger = logging.getLogger(__name__)


class AppBaseModel(BaseModel):
    """
    Pydantic base schema for all application schemas.
    Provides ORM compatibility (from_attributes) for SQLAlchemy result serialisation.
    This is a PYDANTIC class — it has NO __tablename__ and is NOT an ORM model.
    """
    if _HAS_CONFIG_DICT:
        model_config = ConfigDict(from_attributes=True, extra="ignore")
    else:
        class Config:
            orm_mode = True
            extra = "ignore"


class UserSchema(AppBaseModel):
    """Serialised User returned to API clients."""
    id: int
    email: str
    is_active: bool = True


class TokenResponse(AppBaseModel):
    """OAuth2 token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class ErrorResponse(BaseModel):
    """Standard error response envelope."""
    detail: str
    code: Optional[str] = None


class SuccessResponse(BaseModel):
    """Standard success response envelope."""
    message: str
    data: Optional[Dict[str, Any]] = None
