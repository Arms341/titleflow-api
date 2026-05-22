"""
auth/jwt_handler.py - Canonical locked template v1.0.0
JARVIS Locked File Library

Rules:
1. JWT_SECRET, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES ALL imported from config
2. create_access_token uses ACCESS_TOKEN_EXPIRE_MINUTES — never hardcode minutes
3. verify_token catches PyJWTError AND generic Exception — never leaks tracebacks
4. oauth2_scheme defined HERE — not re-declared in auth/dependencies.py
5. No imports from models/, routes/, or database/ — auth is foundation layer

CHANGE LOG:
  v1.0.0 - Initial locked template. Fixes recurring AI bug where
           ACCESS_TOKEN_EXPIRE_MINUTES is used in create_access_token but never
           imported from config, causing NameError caught silently by except
           which returns "" empty token — login appears to succeed but token is
           dead, GV auth cycle reports incomplete at /auth/me (401).
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError

# ALL three constants must be imported — ACCESS_TOKEN_EXPIRE_MINUTES is the
# most commonly dropped one. If it's missing, create_access_token silently
# returns "" and the entire auth cycle breaks without an obvious error.
from config import ALGORITHM, JWT_SECRET, ACCESS_TOKEN_EXPIRE_MINUTES

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Keep a reference to the decode function so tests can monkeypatch it cleanly
_jwt_decode_fn = jwt.decode


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token from the given data dict.

    Reads data dict and optional expiry delta. Uses ACCESS_TOKEN_EXPIRE_MINUTES
    from config as default. Returns encoded JWT string. Returns empty string on
    error (logs the exception — never raises so callers always get a string).
    """
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + (
            expires_delta if expires_delta is not None
            else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode["exp"] = expire
        return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    except Exception as exc:
        logger.error(f"[JWT] create_access_token failed: {exc}")
        return ""


def verify_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token string.

    Returns decoded payload dict if valid and not expired.
    Returns None if token is invalid, expired, or any error occurs.
    """
    try:
        return _jwt_decode_fn(token, JWT_SECRET, algorithms=[ALGORITHM])
    except PyJWTError as exc:
        logger.warning(f"[JWT] Invalid token: {exc}")
        return None
    except Exception as exc:
        logger.error(f"[JWT] verify_token unexpected error: {exc}")
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> dict:
    """FastAPI dependency: decode Bearer token and return payload dict.

    Raises HTTP 401 if token is missing, invalid, or expired.
    Returns decoded payload dict on success.
    """
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload
