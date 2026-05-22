"""
auth/dependencies.py - Canonical locked template v1.2.0
JARVIS Locked File Library — DO NOT MODIFY WITHOUT UPDATING VERSION

v1.2.0: User import moved from models.base to models.user — eliminates
  duplicate __tablename__="users" crash when gig-specific models/user.py exists.
v1.1.0: DEBT-9 FIX-RBAC-DEPENDENCIES — added get_admin_user and get_approved_agent.
  Both use getattr() with safe defaults so they work regardless of what field
  names the AI generated in the ORM model (role vs is_admin, approval_status
  vs is_approved, etc). Universal: works for any RBAC gig type.

Rules enforced by this template:
1. verify_token imported from .jwt_handler — NEVER from .schemas
2. get_current_user is async — always takes oauth2_scheme token + db session
3. get_db imported from database — not from models or config
4. No circular imports — auth/dependencies.py only imports from:
   - database (get_db)
   - models.user (User)
   - auth.jwt_handler (verify_token)
   - fastapi (Depends, HTTPException, status)
   - sqlalchemy.orm (Session)
5. get_admin_user: checks role in (admin, administrator, staff) OR is_admin=True
6. get_approved_agent: checks approval_status == active AND is_active=True
"""
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from auth.jwt_handler import verify_token

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    FastAPI dependency: decode JWT token and return the authenticated user.

    Reads Bearer token from Authorization header via oauth2_scheme and db
    session from get_db. Returns User ORM instance if token valid and user
    exists. Raises HTTP 401 if token invalid, expired, or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_token(token)
        if payload is None:
            raise credentials_exception

        # Support both 'sub' (email) and 'user_id' payload formats
        user_identifier = payload.get("sub") or payload.get("user_id")
        if user_identifier is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    try:
        from models.user import User  # late import to avoid circular deps

        # Try lookup by email first, then by id
        result = None
        try:
            result = db.execute(select(User).where(User.email == user_identifier))
            user = result.scalar_one_or_none()
        except Exception:
            user = None

        if user is None:
            try:
                result = db.execute(select(User).where(User.id == user_identifier))
                user = result.scalar_one_or_none()
            except Exception:
                user = None

        if user is None:
            raise credentials_exception

        return user

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[AUTH] get_current_user failed: {exc}")
        raise credentials_exception


async def get_current_active_user(
    current_user=Depends(get_current_user),
):
    """
    FastAPI dependency: verify current user is active.

    Reads current_user from get_current_user dependency.
    Returns user if active. Raises HTTP 400 if user is inactive.
    """
    is_active = getattr(current_user, "is_active", True)
    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user


async def get_admin_user(
    current_user=Depends(get_current_user),
):
    """
    FastAPI dependency: verify current user has admin privileges.

    DEBT-9 FIX-RBAC-DEPENDENCIES (v1.1.0): Uses getattr() with safe defaults
    so this works regardless of the exact field name the AI chose in the ORM:
      - role field: checks for 'admin', 'administrator', 'staff'
      - is_admin field: boolean flag fallback
    Returns user if admin. Raises HTTP 403 if not admin.
    Universal: works for any RBAC gig — Title Company, Analytics, CRM, etc.
    """
    _role = getattr(current_user, "role", None)
    _is_admin = getattr(current_user, "is_admin", False)
    _is_superuser = getattr(current_user, "is_superuser", False)

    _admin_roles = {"admin", "administrator", "staff", "superuser", "owner"}
    _has_role = isinstance(_role, str) and _role.lower() in _admin_roles

    if not (_has_role or _is_admin or _is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_approved_agent(
    current_user=Depends(get_current_user),
):
    """
    FastAPI dependency: verify current user is an approved agent/staff member.

    DEBT-9 FIX-RBAC-DEPENDENCIES (v1.1.0): Uses getattr() with safe defaults.
    Checks approval_status field (expects 'active') and is_active flag.
    For gigs with agent approval workflows (Title Company, real estate, etc.)
    Returns user if approved and active. Raises HTTP 403 if pending/rejected.
    Universal: degrades gracefully if field does not exist on model.
    """
    _approval = getattr(current_user, "approval_status", "active")
    _is_active = getattr(current_user, "is_active", True)
    _is_approved = getattr(current_user, "is_approved", None)

    # Explicit approval field wins if present
    if _is_approved is not None:
        _approved = bool(_is_approved)
    else:
        _approved = (str(_approval).lower() in {"active", "approved", "verified"})

    if not _approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account pending approval",
        )
    if not _is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    return current_user


def auth_dependency(token: str = Depends(oauth2_scheme)) -> str:
    """
    Lightweight auth dependency: verify token and return user identifier.

    Reads Bearer token from Authorization header.
    Returns user identifier string (email or id) if valid.
    Raises HTTP 403 if token invalid or missing user identifier.
    """
    try:
        payload = verify_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authentication token",
            )
        user_id = payload.get("sub") or payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token does not contain user identifier",
            )
        return str(user_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[AUTH] auth_dependency failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authentication token",
        )
