"""
tests/test_counties.py  v1.0.0
Locked template — JARVIS title_company gig.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

_COUNTY_PAYLOAD = {
    "state": "TX",
    "county_name": "Lubbock",
    "city": "Lubbock",
    "closing_fee_flat": 250.00,
    "recording_fee_flat": 75.00,
    "transfer_tax_rate_pct": 0.0,
    "survey_fee_flat": 450.00,
    "home_warranty_flat": 600.00,
    "simultaneous_issue_discount_flat": 200.00,
    "is_active": True,
}

_COUNTY_UPDATE = {
    "closing_fee_flat": 275.00,
    "recording_fee_flat": 80.00,
}


def test_create_county(client: Any, auth_headers: Any) -> None:
    """POST /counties/ → 201."""
    response = client.post("/counties/", json=_COUNTY_PAYLOAD, headers=auth_headers)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert "id" in data
    logger.info("Created county id=%s", data["id"])


def test_get_county(client: Any, auth_headers: Any, test_db: Any) -> None:
    """GET /counties/{id} → 200."""
    create = client.post("/counties/", json=_COUNTY_PAYLOAD, headers=auth_headers)
    assert create.status_code == 201, f"Setup failed: {create.status_code} {create.text}"
    c_id = create.json()["id"]

    response = client.get(f"/counties/{c_id}", headers=auth_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["id"] == c_id


def test_list_counties(client: Any, auth_headers: Any) -> None:
    """GET /counties/ → 200 list."""
    response = client.get("/counties/", headers=auth_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert isinstance(response.json(), list)


def test_list_counties_filter_by_state(client: Any, auth_headers: Any, test_db: Any) -> None:
    """GET /counties/?state=TX → 200 filtered list."""
    client.post("/counties/", json=_COUNTY_PAYLOAD, headers=auth_headers)
    response = client.get("/counties/?state=TX", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_update_county(client: Any, auth_headers: Any, test_db: Any) -> None:
    """PUT /counties/{id} → 200."""
    create = client.post("/counties/", json=_COUNTY_PAYLOAD, headers=auth_headers)
    assert create.status_code == 201, f"Setup failed: {create.status_code} {create.text}"
    c_id = create.json()["id"]

    response = client.put(f"/counties/{c_id}", json=_COUNTY_UPDATE, headers=auth_headers)
    assert response.status_code == 200


def test_delete_county(client: Any, auth_headers: Any, test_db: Any) -> None:
    """DELETE /counties/{id} → 200."""
    create = client.post("/counties/", json=_COUNTY_PAYLOAD, headers=auth_headers)
    assert create.status_code == 201
    c_id = create.json()["id"]

    delete = client.delete(f"/counties/{c_id}", headers=auth_headers)
    assert delete.status_code == 200

    get_after = client.get(f"/counties/{c_id}", headers=auth_headers)
    assert get_after.status_code == 404
