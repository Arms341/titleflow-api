"""
routes/admin.py  v1.1.0
Admin analytics dashboard + fee settings management.
v1.1.0: Added GET/PUT /admin/fee-settings for configurable fees and toggles.
"""
import json
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
from services.company_service import CompanyService

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


DEFAULT_FEES = {
    "closing_fee_per_side": 300.00,
    "recording_fee": 33.00,
    "deed_prep_fee": 150.00,
    "release_prep_fee": 50.00,
    "tax_cert_fee": 10.00,
    "e_recording_fee_seller": 19.35,
    "e_recording_fee_buyer": 6.45,
    "guaranty_fee": 2.00,
    "survey_fee": 500.00,
    "default_home_warranty": 700.00,
    "appraisal_fee": 550.00,
    "credit_report_fee": 35.00,
    "flood_cert_fee": 20.00,
    "origination_rate_pct": 1.0,
    "default_per_diem_rate_pct": 6.5,
    "title_search_fee_amount": 175.00,
    "custom_fees": [],
    "endorsements": {
        "t19": {"amount": 80.99, "enabled": True, "label": "T-19 Restrictions/Encroachments"},
        "survey_cover": {"amount": 99.15, "enabled": True, "label": "Survey Cover (T-19.1)"},
        "t17": {"amount": 25.00, "enabled": True, "label": "T-17 Access"},
        "t36": {"amount": 25.00, "enabled": True, "label": "T-36 Environmental Lien"},
        "t30": {"amount": 25.00, "enabled": True, "label": "T-30 Mortgagee"}
    },
    "seller_toggles": {
        "recording_fee": True,
        "transfer_tax": True,
        "tax_cert": True,
        "e_recording": True,
        "guaranty_fee": True,
        "home_warranty": True,
        "survey": True,
        "per_diem_interest": True,
        "reissue_discount": False,
        "title_search_fee": False
    }
}


@router.get("/fee-settings")
def get_fee_settings(
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get current fee settings (merged with defaults)."""
    try:
        svc = CompanyService()
        svc._db = db
        company = svc.get_company()
        stored = {}
        if company and company.fee_settings:
            try:
                stored = json.loads(company.fee_settings)
            except (json.JSONDecodeError, TypeError):
                pass
        # Deep merge: defaults + stored overrides
        merged = {**DEFAULT_FEES, **stored}
        if "endorsements" in DEFAULT_FEES:
            merged["endorsements"] = {**DEFAULT_FEES["endorsements"], **stored.get("endorsements", {})}
        if "seller_toggles" in DEFAULT_FEES:
            merged["seller_toggles"] = {**DEFAULT_FEES["seller_toggles"], **stored.get("seller_toggles", {})}
        return merged
    except Exception as exc:
        logger.error(f"[ADMIN] get_fee_settings failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to fetch fee settings")


@router.put("/fee-settings")
def update_fee_settings(
    settings: dict,
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Update fee settings. Saves full JSON blob."""
    try:
        svc = CompanyService()
        svc._db = db
        company = svc.get_company()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        company.fee_settings = json.dumps(settings)
        db.commit()
        db.refresh(company)
        logger.info(f"[ADMIN] Fee settings updated by {current_user.email}")
        return json.loads(company.fee_settings)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[ADMIN] update_fee_settings failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to update fee settings")
