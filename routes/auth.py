"""routes/auth.py — canonical locked template v1.7.0

v1.7.0: Agent self-registration flow:
  - Register sets is_active=False (pending approval)
  - /me allows inactive users to see their status
  - Register sends email notification to admin
  - Approve sends welcome email to agent
v1.6.0: Email case-insensitive.
v1.5.0: Added PUT /profile for agent self-service profile edits.
  Added full profile response on /me (to_profile_dict).
  Added GET /agents (admin list all agents) + PUT /agents/{id}/approve.
  Register now accepts full_name + phone + brokerage_name.
v1.4.0: User import moved from models.base to models.user.
v1.3.0: All handlers sync def (not async def).
v1.2.0: /register uses User.create() classmethod.
v1.1.0: /register accepts JSON body (UserCreate schema).
"""
import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select

from auth.jwt_handler import create_access_token
from auth.dependencies import get_current_active_user, get_current_user, get_admin_user
from auth.schemas import UserCreate, ProfileUpdate
from database import get_db
from models.user import User
from models.base import get_password_hash

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login")
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return JWT access token."""
    try:
        email_normalized = form_data.username.lower().strip()
        result = db.execute(select(User).where(User.email == email_normalized))
        user = result.scalar_one_or_none()
        if user is None or not user.check_password(form_data.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = create_access_token({"sub": user.email, "user_id": user.id})
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[AUTH] login failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        )


@router.post("/token")
def token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2-compatible token endpoint (alias for /login)."""
    try:
        email_normalized = form_data.username.lower().strip()
        result = db.execute(select(User).where(User.email == email_normalized))
        user = result.scalar_one_or_none()
        if user is None or not user.check_password(form_data.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        tok = create_access_token({"sub": user.email, "user_id": user.id})
        return {"access_token": tok, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[AUTH] token endpoint failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Register a new user account. Inactive until admin approves."""
    try:
        normalized_email = user_data.email.lower().strip()
        existing = db.execute(select(User).where(User.email == normalized_email)).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        new_user = User(
            email=normalized_email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            phone=user_data.phone,
            brokerage_name=user_data.brokerage_name,
            role="agent",
            is_active=False,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Notify admin (fire-and-forget)
        def _send_admin_email():
            try:
                from services.email_service import get_email_service
                from services.company_service import CompanyService
                email_svc = get_email_service()
                co_svc = CompanyService()
                co_svc._db = db
                company_row = co_svc.get_company()
                company_dict = {"email": company_row.email, "order_submission_email": getattr(company_row, "order_submission_email", None), "company_name": company_row.company_name}
                agent_dict = {"full_name": new_user.full_name, "email": new_user.email, "brokerage_name": new_user.brokerage_name, "phone": new_user.phone, "license_number": getattr(new_user, "license_number", "")}
                loop = asyncio.new_event_loop()
                loop.run_until_complete(email_svc.notify_new_agent(agent_dict, company_dict))
                loop.close()
            except Exception as e:
                logger.warning("Admin notification email failed: %s", e)
        background_tasks.add_task(_send_admin_email)

        return {"id": new_user.id, "email": new_user.email, "is_active": False, "message": "Registration successful. Awaiting admin approval."}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[AUTH] register failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration service error",
        )


@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    """Return the currently authenticated user full profile (active or pending)."""
    return current_user.to_profile_dict()


@router.put("/profile")
def update_profile(
    profile_data: ProfileUpdate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update the current user profile fields."""
    try:
        update_fields = profile_data.model_dump(exclude_unset=True)
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        for field, value in update_fields.items():
            setattr(current_user, field, value)

        db.commit()
        db.refresh(current_user)
        logger.info(f"[AUTH] Profile updated for user {current_user.id}: {list(update_fields.keys())}")
        return current_user.to_profile_dict()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[AUTH] profile update failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed",
        )


@router.get("/agents")
def list_agents(
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Admin: list all agent accounts."""
    try:
        result = db.execute(
            select(User).where(User.role.in_(["agent", "customer"])).order_by(User.created_at.desc())
        )
        agents = result.scalars().all()
        return [u.to_profile_dict() for u in agents]
    except Exception as exc:
        logger.error(f"[AUTH] list_agents failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to list agents")


@router.put("/agents/{agent_id}/approve")
def approve_agent(
    agent_id: int,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Admin: approve an agent account (set is_active=True, role=agent)."""
    try:
        agent = db.execute(select(User).where(User.id == agent_id)).scalar_one_or_none()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        agent.is_active = True
        agent.role = "agent"
        db.commit()
        db.refresh(agent)
        logger.info(f"[AUTH] Agent {agent_id} approved by admin {current_user.id}")

        # Send welcome email to agent (fire-and-forget)
        def _send_welcome_email():
            try:
                from services.email_service import get_email_service
                from services.company_service import CompanyService
                email_svc = get_email_service()
                co_svc = CompanyService()
                co_svc._db = db
                company_row = co_svc.get_company()
                company_dict = {"company_name": company_row.company_name, "phone": company_row.phone, "email": company_row.email}
                agent_dict = {"email": agent.email, "full_name": agent.full_name}
                loop = asyncio.new_event_loop()
                loop.run_until_complete(email_svc.notify_agent_approved(agent_dict, company_dict))
                loop.close()
            except Exception as e:
                logger.warning("Agent welcome email failed: %s", e)
        background_tasks.add_task(_send_welcome_email)

        return agent.to_profile_dict()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[AUTH] approve_agent failed: {exc}")
        raise HTTPException(status_code=500, detail="Approval failed")


@router.put("/agents/{agent_id}/deactivate")
def deactivate_agent(
    agent_id: int,
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Admin: deactivate an agent account."""
    try:
        agent = db.execute(select(User).where(User.id == agent_id)).scalar_one_or_none()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        agent.is_active = False
        db.commit()
        db.refresh(agent)
        logger.info(f"[AUTH] Agent {agent_id} deactivated by admin {current_user.id}")
        return agent.to_profile_dict()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[AUTH] deactivate_agent failed: {exc}")
        raise HTTPException(status_code=500, detail="Deactivation failed")


@router.post("/agents/create", status_code=status.HTTP_201_CREATED)
def admin_create_agent(
    user_data: UserCreate,
    current_user=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Admin: manually create an agent account (active immediately, no approval needed)."""
    try:
        normalized_email = user_data.email.lower().strip()
        existing = db.execute(select(User).where(User.email == normalized_email)).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(status_code=400, detail="Email already registered")
        new_user = User(
            email=normalized_email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            phone=getattr(user_data, 'phone', None),
            brokerage_name=getattr(user_data, 'brokerage_name', None),
            role="agent",
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"[AUTH] Agent {new_user.id} created by admin {current_user.id}")
        return new_user.to_profile_dict()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[AUTH] admin_create_agent failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to create agent")
