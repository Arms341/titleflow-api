"""
auth/schemas.py - Canonical locked template v1.0.0
JARVIS Locked File Library

Rules:
1. Pydantic v2 schemas ONLY — no JWT logic, no database calls
2. UserSchema, TokenSchema, UserCreate, UserResponse are the standard exports
3. NEVER import from auth.jwt_handler — schemas are data shapes, not logic
4. model_config = ConfigDict(from_attributes=True) — Pydantic v2 compatible
"""
import logging
from typing import Optional

from pydantic import BaseModel, field_validator

try:
    from pydantic import ConfigDict
    _HAS_CONFIG_DICT = True
except ImportError:
    _HAS_CONFIG_DICT = False

logger = logging.getLogger(__name__)


class UserSchema(BaseModel):
    """Pydantic schema for User ORM model serialisation."""
    id: int
    email: str
    is_active: bool = True

    if _HAS_CONFIG_DICT:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class UserCreate(BaseModel):
    """Schema for creating a new user — validates email and password at intake."""
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserResponse(BaseModel):
    """Schema returned to clients — never exposes hashed_password."""
    id: int
    email: str
    is_active: bool = True

    if _HAS_CONFIG_DICT:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


class TokenSchema(BaseModel):
    """OAuth2 token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class TokenData(BaseModel):
    """Decoded JWT payload schema."""
    sub: Optional[str] = None
    user_id: Optional[int] = None
