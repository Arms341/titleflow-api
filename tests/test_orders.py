"""
tests/test_orders.py  v1.0.1
Locked template — JARVIS title_company gig.

v1.0.1: Converted module-level _ORDER_PAYLOAD/_ORDER_UPDATE to function form.
  Added import pytest.
"""
import logging
from typing import Any
import pytest

logger = logging.getLogger(__name__)


def _order_payload() -> dict:
    """Return a valid order create payload. Function form prevents pipeline stripping."""
    return {
        "order_type": "purchase",
        "seller_name": "Jane Seller",
        "buyer_name": "John Buyer",
        "property_address": "123 Main St, Lubbock, TX",
        "estimated_closing_date": "2026-06-15",
        "notes": "Standard residential purchase",
    }


def _order_update() -> dict:
    """Return order update payload."""
    return {
        "lender_name": "West Texas Bank",
        "loan_officer_name": "Bob Loans",
    }


def test_create_order(client: Any, auth_headers: Any) -> None:
    """POST /orders/ → 201 with status=submitted."""
    response = client.post("/orders/", json=_order_payload(), headers=auth_headers)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert "id" in data
    assert data.get("status") == "submitted"


def test_get_order(client: Any, auth_headers: Any, test_db: Any) -> None:
    """GET /orders/{id} → 200."""
    create = client.post("/orders/", json=_order_payload(), headers=auth_headers)
    assert create.status_code == 201
    o_id = create.json()["id"]

    response = client.get(f"/orders/{o_id}", headers=auth_headers)
    assert response.status_code == 200


def test_list_orders(client: Any, auth_headers: Any) -> None:
    """GET /orders/ → 200."""
    response = client.get("/orders/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_order(client: Any, auth_headers: Any, test_db: Any) -> None:
    """PUT /orders/{id} → 200."""
    create = client.post("/orders/", json=_order_payload(), headers=auth_headers)
    o_id = create.json()["id"]

    response = client.put(f"/orders/{o_id}", json=_order_update(), headers=auth_headers)
    assert response.status_code == 200


def test_update_order_status(client: Any, auth_headers: Any, test_db: Any) -> None:
    """PUT /orders/{id}/status → 200 with valid status."""
    create = client.post("/orders/", json=_order_payload(), headers=auth_headers)
    o_id = create.json()["id"]

    response = client.put(f"/orders/{o_id}/status",
                          json={"status": "opened"}, headers=auth_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json().get("status") == "opened"


def test_update_order_status_invalid(client: Any, auth_headers: Any, test_db: Any) -> None:
    """PUT /orders/{id}/status with invalid value → 400."""
    create = client.post("/orders/", json=_order_payload(), headers=auth_headers)
    o_id = create.json()["id"]

    response = client.put(f"/orders/{o_id}/status",
                          json={"status": "bogus"}, headers=auth_headers)
    assert response.status_code == 400


def test_delete_order(client: Any, auth_headers: Any, test_db: Any) -> None:
    """DELETE /orders/{id} → 200."""
    create = client.post("/orders/", json=_order_payload(), headers=auth_headers)
    o_id = create.json()["id"]

    delete_resp = client.delete(f"/orders/{o_id}", headers=auth_headers)
    assert delete_resp.status_code == 200
