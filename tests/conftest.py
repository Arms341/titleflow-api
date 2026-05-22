"""
tests/conftest.py - Deterministic locked template v1.5.0
JARVIS - Never AI-generated.

v1.5.0: Removed app.* fallback imports — project structure is always root-level
  (main.py, database.py, models/base.py). The app.* fallbacks confused the static
  plan analyzer into creating phantom app/ stubs via GPT-REC-C.

v1.4.0: FIX-CONFTEST-STATICPOOL — added poolclass=StaticPool to _test_engine.
  Without StaticPool, SQLite in-memory uses QueuePool which may hand out
  different connections per checkout. Each SQLite in-memory connection is an
  independent database — register() commits user to C1, login() reads from C2
  (empty) → user not found → 401 → test_list_endpoint fails every build.
  StaticPool forces all checkouts to reuse the single underlying connection,
  so all requests within a test see the same in-memory state.
  Also added ("/auth/login", "form") to the login URL list — the OAuth2
  PasswordRequestForm endpoint requires form-encoded data, not JSON.

v1.3.0: DEBT-7 SA 2.0 COMPATIBILITY — removed Session(bind=connection) pattern
  (SA 1.x, raises TypeError in SQLAlchemy 2.0+). Replaced with a clean per-test
  session that uses rollback() for isolation. TestingSessionLocal is configured
  via sessionmaker.configure(bind=engine) rather than passing bind= at call time.
  Compatible with SQLAlchemy 1.4 and 2.0.

v1.2.0: auth_headers tries /auth/register, /auth/login, /auth/token with both
  JSON and form-encoded payloads. Robust across all gig types.
"""
import logging
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from models.base import Base
from database import get_db
from main import app

logger = logging.getLogger(__name__)

TEST_DATABASE_URL = "sqlite:///:memory:"

# FIX-CONFTEST-STATICPOOL (v1.4.0): StaticPool required for SQLite in-memory.
# Without it, QueuePool may hand out different connections per request — each
# SQLite in-memory connection is its own empty database. StaticPool pins all
# checkouts to a single connection so register() and login() share state.
_test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)


@event.listens_for(_test_engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign keys in SQLite test engine."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# SA 2.0 compatible: create factory without bind= at construction time.
# Engine is configured below via sessionmaker.configure() so the factory
# can be imported at module level before the engine connection is made.
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False)
TestingSessionLocal.configure(bind=_test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables once for the test session, drop after."""
    try:
        import models.task  # noqa: F401
        import models.project  # noqa: F401
    except ImportError:
        pass
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture()
def test_db(setup_test_db):
    """SA 2.0 compatible per-test session with rollback isolation.

    DEBT-7: replaces Session(bind=connection) (SA 1.x, broken in 2.0) with a
    plain session from the factory. Rollback on teardown ensures each test
    starts clean without requiring connection-level transaction binding.
    """
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def override_get_db(test_db: Session):
    """Override FastAPI's get_db dependency with the test session."""
    def _get_test_db():
        try:
            yield test_db
        finally:
            pass
    return _get_test_db


@pytest.fixture()
def client(override_get_db):
    """TestClient with overridden DB dependency injected."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client: TestClient) -> dict:
    """Register + login a test user, return Authorization Bearer headers.

    Tries multiple common auth URL patterns so this fixture works across
    all gig types (task management, analytics, title company, CRM, etc.).
    Returns empty dict and logs a warning if auth is unavailable.
    """
    test_email = "testuser@example.com"
    test_password = "TestPassword123!"

    # Step 1: register (ignore 400/409 — user may already exist)
    for url in ["/auth/register", "/api/v1/auth/register", "/users/register"]:
        try:
            r = client.post(url, json={"email": test_email, "password": test_password})
            if r.status_code in (200, 201, 400, 409, 422):
                break
        except Exception:
            continue

    # Step 2: login — try JSON then form-encoded.
    # NOTE: ("/auth/login", "form") MUST be in this list — OAuth2PasswordRequestForm
    # requires form-encoded data. JSON login (/auth/login json) returns 422.
    for url, kind in [
        ("/auth/login", "json"),
        ("/api/v1/auth/login", "json"),
        ("/auth/login", "form"),
        ("/auth/token", "form"),
        ("/token", "form"),
    ]:
        try:
            if kind == "json":
                r = client.post(url, json={"email": test_email, "password": test_password})
            else:
                r = client.post(url, data={"username": test_email, "password": test_password})
            if r.status_code == 200:
                token = r.json().get("access_token") or r.json().get("token")
                if token:
                    return {"Authorization": f"Bearer {token}"}
        except Exception:
            continue

    logger.warning("[CONFTEST] Could not obtain auth token — returning empty headers")
    return {}
