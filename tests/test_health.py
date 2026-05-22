"""
tests/test_health.py - Deterministic locked template v1.0.0
JARVIS Locked File Library — DO NOT MODIFY WITHOUT UPDATING VERSION

Validates the root / and /health endpoints.

Accepts BOTH "ok" and "healthy" as valid status values since different
AI-generated main.py versions use either string. Checks presence and
structure only — never hardcodes a single status string.

CHANGE LOG:
  v1.0.0 - Initial locked template.
"""
import logging

import pytest
from fastapi.testclient import TestClient

logger = logging.getLogger(__name__)

_VALID_STATUSES = {"ok", "healthy", "running", "up"}


def test_health_check(client: TestClient) -> None:
    """GET /health returns 200 with a valid status field."""
    try:
        response = client.get("/health")
        assert response.status_code == 200, (
            f"Expected 200 on GET /health, got {response.status_code}: {response.text}"
        )
        data = response.json()
        assert isinstance(data, dict), "Health response should be a JSON object"
        assert "status" in data, "Health response missing 'status' field"
        assert data["status"].lower() in _VALID_STATUSES, (
            f"Health status '{data['status']}' not in expected values {_VALID_STATUSES}"
        )
        logger.info("test_health_check passed — status=%s", data["status"])
    except AssertionError as exc:
        logger.error("[TEST] test_health_check failed: %s", exc)
        raise


def test_health_returns_json(client: TestClient) -> None:
    """GET /health response body is valid JSON with at least one field."""
    try:
        response = client.get("/health")
        assert response.status_code == 200, (
            f"Expected 200 on GET /health, got {response.status_code}"
        )
        data = response.json()
        assert isinstance(data, dict), "Health response should be a dict"
        assert len(data) >= 1, "Health response dict should have at least one field"
        logger.info("test_health_returns_json passed")
    except AssertionError as exc:
        logger.error("[TEST] test_health_returns_json failed: %s", exc)
        raise


def test_root_endpoint(client: TestClient) -> None:
    """GET / returns 200 with valid JSON."""
    try:
        response = client.get("/")
        assert response.status_code == 200, (
            f"Expected 200 on GET /, got {response.status_code}: {response.text}"
        )
        data = response.json()
        assert isinstance(data, dict), "Root endpoint should return a JSON object"
        logger.info("test_root_endpoint passed")
    except AssertionError as exc:
        logger.error("[TEST] test_root_endpoint failed: %s", exc)
        raise
