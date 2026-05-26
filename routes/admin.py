"""
routes/admin.py  v1.0.0
Admin analytics dashboard endpoints.
Provides agent activity stats, sheets/orders metrics, top agents.
"""
import logging
from datetime import datetime, timedelta

from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from auth.dependencies import get_admin_user
from models.user import User
from models.saved_sheet import SavedSheet
from models.order import Order

logger = logging.getLogger(__name__)
router = APIRouter(tags=["admin"])


@router.get("/stats")
def admin_stats(
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Admin dashboard overview stats."""
    try:
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        total_agents = db.execute(
            select(func.count(User.id)).where(User.role.in_(["agent", "customer"]))
        ).scalar() or 0

        active_agents = db.execute(
            select(func.count(User.id)).where(
                User.role.in_(["agent", "customer"]),
                User.is_active == True,
            )
        ).scalar() or 0

        pending_agents = db.execute(
            select(func.count(User.id)).where(
                User.role.in_(["agent", "customer"]),
                User.is_active == False,
            )
        ).scalar() or 0

        total_sheets = db.execute(select(func.count(SavedSheet.id))).scalar() or 0
        sheets_this_week = db.execute(
            select(func.count(SavedSheet.id)).where(SavedSheet.created_at >= week_ago)
        ).scalar() or 0
        sheets_this_month = db.execute(
            select(func.count(SavedSheet.id)).where(SavedSheet.created_at >= month_ago)
        ).scalar() or 0

        total_orders = db.execute(select(func.count(Order.id))).scalar() or 0
        orders_this_week = db.execute(
            select(func.count(Order.id)).where(Order.created_at >= week_ago)
        ).scalar() or 0
        orders_this_month = db.execute(
            select(func.count(Order.id)).where(Order.created_at >= month_ago)
        ).scalar() or 0

        pending_orders = db.execute(
            select(func.count(Order.id)).where(
                Order.status.in_(["pending", "submitted"])
            )
        ).scalar() or 0

        conversion_rate = 0.0
        if total_sheets > 0:
            conversion_rate = round((total_orders / total_sheets) * 100, 1)

        return {
            "agents": {
                "total": total_agents,
                "active": active_agents,
                "pending_approval": pending_agents,
            },
            "sheets": {
                "total": total_sheets,
                "this_week": sheets_this_week,
                "this_month": sheets_this_month,
            },
            "orders": {
                "total": total_orders,
                "this_week": orders_this_week,
                "this_month": orders_this_month,
                "pending": pending_orders,
            },
            "conversion_rate": conversion_rate,
        }
    except Exception as exc:
        logger.error(f"[ADMIN] stats failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to fetch stats")


@router.get("/top-agents")
def top_agents(
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Top agents by sheet + order volume."""
    try:
        results = db.execute(
            select(
                User.id,
                User.email,
                User.full_name,
                User.brokerage_name,
                func.count(SavedSheet.id).label("sheet_count"),
            )
            .outerjoin(SavedSheet, SavedSheet.agent_id == User.id)
            .where(User.role.in_(["agent", "customer"]))
            .group_by(User.id, User.email, User.full_name, User.brokerage_name)
            .order_by(func.count(SavedSheet.id).desc())
            .limit(20)
        ).all()

        agents = []
        for row in results:
            order_count = db.execute(
                select(func.count(Order.id)).where(Order.agent_id == row.id)
            ).scalar() or 0
            agents.append({
                "id": row.id,
                "email": row.email,
                "full_name": row.full_name,
                "brokerage_name": row.brokerage_name,
                "sheet_count": row.sheet_count,
                "order_count": order_count,
            })

        return agents
    except Exception as exc:
        logger.error(f"[ADMIN] top_agents failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to fetch top agents")
