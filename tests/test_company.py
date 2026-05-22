"""
tests/test_company.py  v1.0.0
Locked template — JARVIS title_company gig.
Singleton — test get returns 200, update applies changes, get is public.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

_COMPANY_UPDATE = {
    "company_name": "Hub City Title Agents",
    "phone": "806-555-0100",
    "email": "hello@hubcitytitle.com",
    "tagline": "Your West Texas title experts",
    "primary_color": "#1e3a8a",
    "secondary_color": "#f59e0b",
    "order_submission_email": "orders@hubcitytitle.com",
}


def test_get_company_public(client: Any) -> None:
    """GET /company/ — no auth required."""
    response = client.get("/company/")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "id" in data
    assert "company_name" in data
    logger.info("Fetched company id=%s", data["id"])


def test_update_company(client: Any, auth_headers: Any, test_db: Any) -> None:
    """PUT /company/ → 200 — admin updates branding."""
    response = client.put("/company/", json=_COMPANY_UPDATE, headers=auth_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data.get("company_name") == _COMPANY_UPDATE["company_name"]
    logger.info("Updated company to %s", data.get("company_name"))


def test_get_company_after_update(client: Any, auth_headers: Any, test_db: Any) -> None:
    """GET /company/ returns the updated values."""
    client.put("/company/", json=_COMPANY_UPDATE, headers=auth_headers)
    response = client.get("/company/")
    assert response.status_code == 200
    data = response.json()
    assert data.get("company_name") == _COMPANY_UPDATE["company_name"]
