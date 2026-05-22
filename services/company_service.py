"""
services/company_service.py  v1.0.0
Locked template — JARVIS title_company gig.
Company singleton — auto-creates on first access, only one row ever.
"""
import logging
from typing import Optional

from database import get_db
from fastapi import Depends
from models.company import Company
from schemas.company import CompanyCreate, CompanyUpdate
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Service-layer error."""
    pass


class CompanyService:
    """Business logic for company singleton."""

    def get_or_create(self, db: Session = None) -> Company:
        """Return the singleton row, creating a default if missing."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            existing = db.execute(select(Company).limit(1)).scalars().first()
            if existing:
                return existing
            company = Company(
                company_name="Title Company",
                primary_color="#1e3a8a",
                secondary_color="#f59e0b",
            )
            db.add(company)
            db.commit()
            db.refresh(company)
            logger.info("Auto-created company singleton id=%d", company.id)
            return company
        except Exception as e:
            db.rollback()
            logger.error("Failed to get_or_create company: %s", e)
            raise ServiceError(f"Failed to get company: {e}") from e

    def get_company(self, db: Session = None) -> Company:
        """Return the singleton (auto-create if missing)."""
        return self.get_or_create(db=db)

    def create_company(self, data: CompanyCreate, db: Session = None) -> Company:
        """Upsert-style create — if row exists, update it instead."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            existing = db.execute(select(Company).limit(1)).scalars().first()
            if existing:
                for key, value in data.model_dump(exclude_none=True).items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                db.commit()
                db.refresh(existing)
                logger.info("Updated existing company singleton id=%d", existing.id)
                return existing

            valid_cols = {c.name for c in Company.__table__.columns}
            company = Company(**{
                k: v for k, v in data.model_dump(exclude_none=True).items()
                if k in valid_cols
            })
            db.add(company)
            db.commit()
            db.refresh(company)
            logger.info("Created company singleton id=%d", company.id)
            return company
        except Exception as e:
            db.rollback()
            logger.error("Failed to create company: %s", e)
            raise ServiceError(f"Failed to create company: {e}") from e

    def update_company(self, data: CompanyUpdate, db: Session = None) -> Company:
        """Update the singleton (creating it first if missing)."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            company = self.get_or_create(db=db)
            for key, value in data.model_dump(exclude_unset=True).items():
                if hasattr(company, key):
                    setattr(company, key, value)
            db.commit()
            db.refresh(company)
            logger.info("Updated company singleton id=%d", company.id)
            return company
        except Exception as e:
            db.rollback()
            logger.error("Failed to update company: %s", e)
            raise ServiceError(f"Failed to update company: {e}") from e

    def get_company_by_id(self, id: int, db: Session = None) -> Optional[Company]:
        """Satisfies scaffolded AI route patterns."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            return db.get(Company, id)
        except Exception as e:
            logger.error("Failed to get company %d: %s", id, e)
            raise ServiceError(f"Failed to get company: {e}") from e

    def list_companies(self, skip: int = 0, limit: int = 100,
                       db: Session = None) -> list:
        """Always returns the singleton in a list."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            return [self.get_or_create(db=db)]
        except Exception as e:
            logger.error("Failed to list companies: %s", e)
            raise ServiceError(f"Failed to list companies: {e}") from e

    def delete_company(self, id: int, db: Session = None) -> bool:
        """Singleton cannot be deleted; always returns False."""
        return False

    # Aliases
    create = create_company
    get_by_id = get_company_by_id
    list_all = list_companies
    list = list_companies
    get_all = list_companies
    update = update_company
    delete = delete_company
    get = get_company_by_id


def get_company_service(db: Session = Depends(get_db)) -> CompanyService:
    """FastAPI dependency."""
    inst = CompanyService()
    inst._db = db
    return inst
