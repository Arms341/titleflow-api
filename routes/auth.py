"""routes/auth.py — canonical locked template v1.6.0

Mounts at prefix="/auth" via main.py include_router.
Endpoints: POST /auth/login, POST /auth/register, POST /auth/token,
           GET /auth/me, PUT /auth/profile, GET /auth/agents, PUT /auth/agents/{id}/approve

v1.6.0: Email case-insensitive — all login/token/register normalize to .lower().strip().
v1.5.0: Added PUT /profile for agent self-service profile edits.
  Added full profile response on /me (to_profile_dict).
  Added GET /agents (admin list all agents) + PUT /agents/{id}/approve.
  Register now accepts full_name + phone + brokerage_name.
v1.4.0: User import moved from models.base to models.user.
v1.3.0: All handlers sync def (not async def).
v1.2.0: /register uses User.create() classmethod.
v1.1.0: /register accepts JSON body (UserCreate schema).
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select

from auth.jwt_handler import create_access_token
from auth.dependencies import get_current_active_user, get_admin_user
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
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
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
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"id": new_user.id, "email": new_user.email}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[AUTH] register failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration service error",
        )


@router.get("/me")
def get_me(current_user=Depends(get_current_active_user)):
    """Return the currently authenticated user full profile."""
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
