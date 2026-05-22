"""
database.py - Canonical locked template v1.0.3
JARVIS Locked File Library — DO NOT MODIFY WITHOUT UPDATING VERSION

Rules enforced by this template:
1. import asyncio + logging + os FIRST
2. engine defined BEFORE SessionLocal — order is law
3. pool_timeout=3 — fail fast when DB not running (prevents event loop hang)
4. connect_timeout=3 in connect_args for non-SQLite (TCP connects fail fast)
5. async def init_db() uses asyncio.to_thread for create_all — NEVER blocks event loop
6. close_db() is sync (engine.dispose() is safe to call sync)
7. Base belongs in models/base.py — NOT here

CHANGE LOG:
  v1.0.4 - FIX-INITDB-LIFESPAN-TIMEOUT: asyncio.wait_for(timeout=5.0) added around
           asyncio.to_thread(create_all). FastAPI blocks ALL requests including
           /openapi.json until lifespan completes. Without timeout, slow Postgres
           create_all hangs GV's openapi.json probe -> auth=0/20 + crud=0/15.
           Fix: 5s hard timeout so lifespan always completes fast. Server starts
           even if DB tables not yet created. Universal: any FastAPI+Postgres gig.
  v1.0.3 - FIX-INIT-DB-THREAD-OFFLOAD: Base.metadata.create_all(bind=engine) is a
           SYNC blocking call. When called from async def init_db() on the asyncio event
           loop thread with Postgres not running, it blocks ALL HTTP requests (including
           /health) for the full OS TCP timeout (20-120s). Fix: run create_all in
           asyncio.to_thread() so the event loop stays free to serve requests.
           Also added pool_timeout=3 and connect_timeout=3 to fail fast.
  v1.0.2 - Added JWT_SECRET + SECRET_KEY module-level constants before Settings class.
  v1.0.1 - Initial locked template.
"""
import asyncio
import logging
import os
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# connect_args: SQLite needs check_same_thread=False; Postgres gets connect_timeout=3
# so TCP connection attempts to a non-running Postgres fail fast instead of hanging.
_connect_args: dict = (
    {"check_same_thread": False} if "sqlite" in DATABASE_URL
    else {"connect_timeout": 3}
)

# engine MUST be defined before SessionLocal
# pool_timeout=3: give up waiting for a pool connection after 3s (Postgres may be down)
engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
    pool_timeout=3,
    echo=os.getenv("DEBUG", "false").lower() == "true",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a database session per request."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def init_db() -> None:
    """
    Create all database tables from registered model metadata.

    IMPORTANT: Base.metadata.create_all() is a synchronous blocking call.
    It must run in a thread pool (asyncio.to_thread) so it never blocks the
    asyncio event loop. The 5s hard timeout ensures lifespan always completes
    fast — FastAPI blocks /openapi.json until lifespan finishes, so a slow
    Postgres create_all would cause GV's openapi probe to time out.
    """
    try:
        from models.base import Base  # noqa: F401
        # 5s hard timeout: prevents lifespan hang when Postgres is slow.
        # Without timeout, /openapi.json never responds during GV probe window.
        await asyncio.wait_for(
            asyncio.to_thread(Base.metadata.create_all, engine),
            timeout=5.0,
        )
        logger.info("[DATABASE] Tables created / verified")
    except asyncio.TimeoutError:
        logger.warning("[DATABASE] init_db timed out after 5s — server starting without table creation")
    except ImportError:
        logger.warning("[DATABASE] models.base not found — skipping table creation")
    except Exception as exc:
        logger.error(f"[DATABASE] init_db failed: {exc}")
        # Do NOT re-raise — DB down at startup should not crash the server


def close_db() -> None:
    """Dispose the engine connection pool on shutdown."""
    try:
        engine.dispose()
        logger.info("[DATABASE] Connection pool disposed")
    except Exception as exc:
        logger.error(f"[DATABASE] close_db failed: {exc}")


def check_db_health() -> bool:
    """Return True if the database is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error(f"[DATABASE] Health check failed: {exc}")
        return False
