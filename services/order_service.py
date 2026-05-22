"""
services/order_service.py  v1.0.0
Locked template — JARVIS title_company gig.
Order CRUD + status workflow. Status transitions logged.
"""
import logging
from typing import List, Optional

from database import get_db
from fastapi import Depends
from models.order import Order
from schemas.order import OrderCreate, OrderUpdate
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


VALID_STATUSES = {"submitted", "opened", "in_progress", "closed", "cancelled"}


class ServiceError(Exception):
    """Service-layer error."""
    pass


class OrderService:
    """Business logic for order CRUD + status workflow."""

    def create_order(self, data: OrderCreate, agent_id: Optional[int] = None,
                     db: Session = None) -> Order:
        """Create a new title order with status=submitted."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            valid_cols = {c.name for c in Order.__table__.columns}
            payload = {k: v for k, v in data.model_dump(exclude_none=True).items()
                       if k in valid_cols}
            if agent_id is not None:
                payload["agent_id"] = agent_id
            payload.setdefault("status", "submitted")
            order = Order(**payload)
            db.add(order)
            db.commit()
            db.refresh(order)
            logger.info("Created order id=%d status=%s", order.id, order.status)
            return order
        except Exception as e:
            db.rollback()
            logger.error("Failed to create order: %s", e)
            raise ServiceError(f"Failed to create order: {e}") from e

    def get_order_by_id(self, id: int, db: Session = None) -> Optional[Order]:
        """Get order by id."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            return db.get(Order, id)
        except Exception as e:
            logger.error("Failed to get order %d: %s", id, e)
            raise ServiceError(f"Failed to get order: {e}") from e

    def list_orders(self, skip: int = 0, limit: int = 100,
                    agent_id: Optional[int] = None, status: Optional[str] = None,
                    db: Session = None) -> List[Order]:
        """List orders with optional filters."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            stmt = select(Order)
            if agent_id is not None:
                stmt = stmt.where(Order.agent_id == agent_id)
            if status is not None:
                stmt = stmt.where(Order.status == status)
            stmt = stmt.order_by(Order.created_at.desc()).offset(skip).limit(limit)
            return list(db.execute(stmt).scalars().all())
        except Exception as e:
            logger.error("Failed to list orders: %s", e)
            raise ServiceError(f"Failed to list orders: {e}") from e

    def update_order(self, id: int, data: OrderUpdate, db: Session = None) -> Optional[Order]:
        """Update an existing order."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            order = db.get(Order, id)
            if not order:
                return None
            for key, value in data.model_dump(exclude_unset=True).items():
                if hasattr(order, key):
                    setattr(order, key, value)
            db.commit()
            db.refresh(order)
            logger.info("Updated order id=%d", id)
            return order
        except Exception as e:
            db.rollback()
            logger.error("Failed to update order %d: %s", id, e)
            raise ServiceError(f"Failed to update order: {e}") from e

    def update_status(self, id: int, new_status: str, db: Session = None) -> Optional[Order]:
        """Admin-only status transition. Validates status is in VALID_STATUSES."""
        db = db if db is not None else getattr(self, "_db", None)
        if new_status not in VALID_STATUSES:
            raise ServiceError(f"Invalid status: {new_status}. Must be one of {VALID_STATUSES}")
        try:
            order = db.get(Order, id)
            if not order:
                return None
            old_status = order.status
            order.status = new_status
            db.commit()
            db.refresh(order)
            logger.info("Order %d status: %s -> %s", id, old_status, new_status)
            return order
        except Exception as e:
            db.rollback()
            logger.error("Failed to update order %d status: %s", id, e)
            raise ServiceError(f"Failed to update order status: {e}") from e

    def delete_order(self, id: int, db: Session = None) -> bool:
        """Delete an order."""
        db = db if db is not None else getattr(self, "_db", None)
        try:
            order = db.get(Order, id)
            if not order:
                return False
            db.delete(order)
            db.commit()
            logger.info("Deleted order id=%d", id)
            return True
        except Exception as e:
            db.rollback()
            logger.error("Failed to delete order %d: %s", id, e)
            raise ServiceError(f"Failed to delete order: {e}") from e

    # Aliases
    create = create_order
    get_by_id = get_order_by_id
    list_all = list_orders
    list = list_orders
    get_all = list_orders
    update = update_order
    delete = delete_order
    get = get_order_by_id


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    """FastAPI dependency."""
    inst = OrderService()
    inst._db = db
    return inst
