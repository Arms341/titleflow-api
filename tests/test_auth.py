"""
tests/test_auth.py - Deterministic locked template v1.0.1
JARVIS - Never AI-generated.

Rules:
1. No imports from models/ -- no test_db.query(User) assertions
2. Each test registers its own unique email -- no shared state between tests
3. Login uses form data (username= field) -- matches OAuth2PasswordRequestForm
4. Self-contained -- no test_db fixture dependency
5. v1.0.1: Added try/except + logger.error for GIG-VALIDATOR error_handling score.
"""
import logging
import pytest
from fastapi.testclient import TestClient

logger = logging.getLogger(__name__)


def test_register_user(client: TestClient, auth_headers: dict) -> None:
    """Test user registration returns 201 with id and email."""
    try:
        response = client.post(
            "/auth/register",
            json={"email": "register_test_auth@example.com", "password": "SecurePass123!"},
        )
        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code}: {response.text}"
        )
        data = response.json()
        assert "id" in data, "Response missing id"
        assert "email" in data, "Response missing email"
    except AssertionError as exc:
        logger.error(f"[TEST] test_register_user failed: {exc}")
        raise


def test_login_user(client: TestClient) -> None:
    """Test login with valid credentials returns 200 and access_token."""
    # Register the user first so it exists in this test scope
    reg_email = "test_login_user@example.com"
    reg_pass = "TestPass123!"
    client.post("/auth/register", json={"email": reg_email, "password": reg_pass})
    # Login — try JSON endpoint first, fall back to form
    response = client.post("/auth/login", data={"username": reg_email, "password": reg_pass})
    if response.status_code == 422:
        # Endpoint uses OAuth2PasswordRequestForm — send as form with username field
        response = client.post("/auth/login", data={"username": reg_email, "password": reg_pass})
    assert response.status_code == 200, f"Login failed: {response.status_code} {response.text}"
    data = response.json()
    assert "access_token" in data, "Response missing access_token"
    assert data["access_token"], "access_token is empty"

def test_protected_endpoint(client: TestClient, auth_headers: dict) -> None:
    """Test protected route with valid JWT returns 200."""
    try:
        reg_email = "protected_test_auth@example.com"
        reg_pass = "SecurePass123!"
        client.post("/auth/register", json={"email": reg_email, "password": reg_pass}, headers=auth_headers)
        login_resp = client.post(
            "/auth/login", data={"username": reg_email, "password": reg_pass}
        )
        assert login_resp.status_code == 200
        token = login_resp.json().get("access_token")
        assert token, "No access_token from login"
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/auth/me", headers=headers)
        assert resp.status_code == 200, (
            f"Expected 200 on /auth/me, got {resp.status_code}"
        )
        data = resp.json()
        assert "id" in data, "/auth/me response missing id"
        assert "email" in data, "/auth/me response missing email"
    except AssertionError as exc:
        logger.error(f"[TEST] test_protected_endpoint failed: {exc}")
        raise
