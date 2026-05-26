"""
auth/schemas.py - Canonical locked template v1.1.0
JARVIS Locked File Library

v1.1.0: Added ProfileUpdate schema for PUT /auth/profile.
  Added full_name, phone, brokerage_name to UserCreate for registration.
  Added UserProfileResponse for full /me response.
v1.0.0: Initial schemas (UserSchema, TokenSchema, UserCreate, UserResponse).

Rules:
1. Pydantic v2 schemas ONLY — no JWT logic, no database calls
2. NEVER import from auth.jwt_handler — schemas are data shapes, not logic
3. model_config = ConfigDict(from_attributes=True) — Pydantic v2 compatible
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
    full_name: Optional[str] = None
    phone: Optional[str] = None
    brokerage_name: Optional[str] = None

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


class ProfileUpdate(BaseModel):
    """Schema for PUT /auth/profile — agent self-service profile edits."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    brokerage_name: Optional[str] = None
    license_number: Optional[str] = None
    avatar_url: Optional[str] = None

    if _HAS_CONFIG_DICT:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


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


class UserProfileResponse(BaseModel):
    """Full profile response for /auth/me."""
    id: int
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: bool = True
    avatar_url: Optional[str] = None
    brokerage_name: Optional[str] = None
    license_number: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

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
