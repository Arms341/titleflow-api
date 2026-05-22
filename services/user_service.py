"""
services/user_service.py  v1.0.0
Locked template — JARVIS food_truck_pos gig.
CRUD service for User entity (admin user management).
"""
import logging
from typing import List, Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from models.user import User

logger = logging.getLogger(__name__)


class UserService:
    """Service layer for User CRUD operations."""

    def __init__(self, db: Session = None):
        self.db = db

    def create(self, data: dict) -> User:
        user = User(**data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).offset(skip).limit(limit).all()

    def update(self, user_id: int, data: dict) -> Optional[User]:
        user = self.get_by_id(user_id)
        if not user:
            return None
        for key, value in data.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user_id: int) -> bool:
        user = self.get_by_id(user_id)
        if not user:
            return False
        self.db.delete(user)
        self.db.commit()
        return True


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """FastAPI dependency: returns UserService with db injected."""
    return UserService(db)
