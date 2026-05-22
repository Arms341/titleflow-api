"""
tests/test_countys.py  v1.0.0
Locked template — JARVIS real_estate_title_company gig.
Tests CRUD for /countys/ endpoint with proper county schema fields.
"""
import logging
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _county_payload() -> dict:
    """Generate a unique county test payload matching CountyCreate schema."""
    uid = uuid.uuid4().hex[:6]
    return {
        "state": "TX",
        "county_name": f"Test County {uid}",
        "city": "Lubbock",
        "closing_fee_flat": "250.00",
        "recording_fee_flat": "75.00",
        "transfer_tax_rate_pct": "0.50",
        "survey_fee_flat": "350.00",
        "home_warranty_flat": "450.00",
        "simultaneous_issue_discount_flat": "25.00",
        "owner_rate_table_id": 1,
        "lender_rate_table_id": 1,
        "is_active": True,
    }


def test_create_county(client: TestClient, auth_headers: dict) -> None:
    """Test creating a county via POST /countys/."""
    data = _county_payload()
    response = client.post("/countys/", json=data, headers=auth_headers)
    assert response.status_code in (200, 201), (
        f"Expected 200/201, got {response.status_code}: {response.text}"
    )
    body = response.json()
    assert "id" in body, "Response should contain county ID"
    assert body["state"] == data["state"]
    assert body["county_name"] == data["county_name"]
    logger.info("Created county %s", body["id"])


def test_list_counties(client: TestClient, auth_headers: dict) -> None:
    """Test listing counties via GET /countys/."""
    response = client.get("/countys/", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)


def test_get_county(client: TestClient, auth_headers: dict) -> None:
    """Test get county by ID via GET /countys/{id}."""
    data = _county_payload()
    create = client.post("/countys/", json=data, headers=auth_headers)
    assert create.status_code in (200, 201)
    county_id = create.json()["id"]

    get_resp = client.get(f"/countys/{county_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == county_id


def test_update_county(client: TestClient, auth_headers: dict) -> None:
    """Test updating a county via PUT /countys/{id}."""
    data = _county_payload()
    create = client.post("/countys/", json=data, headers=auth_headers)
    assert create.status_code in (200, 201)
    county_id = create.json()["id"]

    update_data = {"county_name": "Updated County", "state": "NY"}
    update = client.put(f"/countys/{county_id}", json=update_data, headers=auth_headers)
    assert update.status_code == 200
    assert update.json()["state"] == "NY"


def test_delete_county(client: TestClient, auth_headers: dict) -> None:
    """Test deleting a county via DELETE /countys/{id}."""
    data = _county_payload()
    create = client.post("/countys/", json=data, headers=auth_headers)
    assert create.status_code in (200, 201)
    county_id = create.json()["id"]

    delete = client.delete(f"/countys/{county_id}", headers=auth_headers)
    assert delete.status_code in (200, 204)

    get_resp = client.get(f"/countys/{county_id}", headers=auth_headers)
    assert get_resp.status_code == 404
