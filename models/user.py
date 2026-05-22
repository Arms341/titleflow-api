"""
models/user.py  v1.1.0
Locked template — JARVIS food_truck_pos gig.
User entity for food truck multi-role auth.

v1.1.0: Added check_password(), get_by_email(), get_by_id(), create() methods.
  Without check_password(), routes/auth.py login returns 500 every build.
  Methods match models_user_universal.py contract but keep food truck columns.
v1.0.0: Initial food truck user model (bare ORM, no methods).
"""
import logging
from datetime import datetime
from typing import Optional

from models.base import Base, get_password_hash, verify_password
from sqlalchemy import Boolean, Column, DateTime, Integer, String, select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class User(Base):
    """SQLAlchemy ORM model for the users table."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False, server_default="")
    full_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    role = Column(String(50), nullable=False, server_default="customer")
    is_active = Column(Boolean, nullable=False, server_default="1")
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"

    def check_password(self, plain_password: str) -> bool:
        """Verify a password against this user's stored hash."""
        return verify_password(plain_password, self.hashed_password)

    @classmethod
    def get_by_email(cls, db: Session, email: str) -> Optional["User"]:
        """Return User with given email or None."""
        try:
            result = db.execute(select(cls).where(cls.email == email))
            return result.scalar_one_or_none()
        except Exception as exc:
            logger.error(f"[USER] get_by_email failed: {exc}")
            return None

    @classmethod
    def get_by_id(cls, db: Session, user_id: int) -> Optional["User"]:
        """Return User with given id or None."""
        try:
            result = db.execute(select(cls).where(cls.id == user_id))
            return result.scalar_one_or_none()
        except Exception as exc:
            logger.error(f"[USER] get_by_id failed: {exc}")
            return None

    @classmethod
    def create(cls, db: Session, email: str, password: str, is_active: bool = True) -> "User":
        """Create and persist a new User with a hashed password."""
        existing = cls.get_by_email(db, email)
        if existing:
            raise ValueError(f"User with email '{email}' already exists")
        user = cls(
            email=email.lower().strip(),
            hashed_password=get_password_hash(password),
            is_active=is_active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"[USER] Created user id={user.id} email={user.email!r}")
        return user
