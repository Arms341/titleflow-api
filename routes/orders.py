"""
routes/orders.py  v1.0.0
Locked template — JARVIS title_company gig.
Order CRUD + admin status update endpoint.
"""
import logging
from typing import List, Optional

from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
    OrderUpdate,
)
from services.order_service import OrderService, ServiceError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["orders"])


def _get_order_service(db: Session = Depends(get_db)) -> OrderService:
    """Inline factory."""
    inst = OrderService()
    inst._db = db
    return inst


@router.get("/", response_model=List[OrderResponse])
def list_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None),
    service: OrderService = Depends(_get_order_service),
) -> List[OrderResponse]:
    """GET /orders/."""
    try:
        return service.list_all(skip=skip, limit=limit, status=status)
    except Exception as e:
        logger.error("Error listing orders: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    service: OrderService = Depends(_get_order_service),
) -> OrderResponse:
    """GET /orders/{id}."""
    try:
        order = service.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching order %d: %s", order_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=OrderResponse, status_code=201)
def create_order(
    data: OrderCreate,
    service: OrderService = Depends(_get_order_service),
) -> OrderResponse:
    """POST /orders/ — agent submits a title order."""
    try:
        return service.create(data)
    except Exception as e:
        logger.error("Error creating order: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    data: OrderUpdate,
    service: OrderService = Depends(_get_order_service),
) -> OrderResponse:
    """PUT /orders/{id}."""
    try:
        updated = service.update(order_id, data)
        if not updated:
            raise HTTPException(status_code=404, detail="Order not found")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating order %d: %s", order_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    service: OrderService = Depends(_get_order_service),
) -> OrderResponse:
    """PUT /orders/{id}/status — admin status workflow."""
    try:
        updated = service.update_status(order_id, payload.status)
        if not updated:
            raise HTTPException(status_code=404, detail="Order not found")
        return updated
    except HTTPException:
        raise
    except ServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error updating order %d status: %s", order_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{order_id}", status_code=200)
def delete_order(
    order_id: int,
    service: OrderService = Depends(_get_order_service),
) -> bool:
    """DELETE /orders/{id}."""
    try:
        deleted = service.delete(order_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Order not found")
        return True
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting order %d: %s", order_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


orders_router = router  # FIX-ROUTER-ALIAS
