"""routes/auth.py — canonical locked template v1.4.0

Mounts at prefix="/auth" via main.py include_router.
Endpoints: POST /auth/login, POST /auth/register, POST /auth/token
router = APIRouter() — NO prefix here, main.py owns the /auth mount.

v1.4.0: User import moved from models.base to models.user — eliminates
  "cannot import name 'User' from 'models.base'" crash after v1.1.0 base.py
  refactor that extracted User to its own module.
v1.3.0: All handlers sync def (not async def). Sync SQLAlchemy Session +
  async def blocks uvicorn event loop → ALL routes timeout → 0/100.
  FastAPI auto-runs sync defs in threadpool. Root cause of build_food_0513_1007.
v1.2.0: /register uses User.create() classmethod (handles hashing + commit).
  v1.1.0 called .set_password() which doesn't exist on User → 500.
v1.1.0: /register accepts JSON body (UserCreate schema) instead of OAuth2 form.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from auth.jwt_handler import create_access_token
from auth.dependencies import get_current_active_user
from auth.schemas import UserCreate
from database import get_db
from models.user import User
from models.base import get_password_hash
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login")
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return JWT access token."""
    try:
        result = db.execute(select(User).where(User.email == form_data.username))
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
        result = db.execute(select(User).where(User.email == form_data.username))
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
        existing = db.execute(select(User).where(User.email == user_data.email)).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        new_user = User(
            email=user_data.email.lower().strip(),
            hashed_password=get_password_hash(user_data.password),
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
    """Return the currently authenticated user profile."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": getattr(current_user, "is_active", True),
    }
