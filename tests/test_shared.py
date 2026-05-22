"""
tests/test_shared.py  v1.0.3
Locked template — JARVIS title_company gig.
Verifies public share route works without auth and includes branding.

v1.0.3: Try-both-URLs pattern (underscore then hyphen). No main.py import.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

_SHEET_PAYLOAD = {
    "sheet_type": "seller_net_sheet",
    "property_address": "123 Main St",
    "property_city": "Lubbock",
    "client_name": "Jane Seller",
    "input_data": {"sale_price": "400000.00"},
    "output_data": {"net_proceeds": "121564.38"},
}


def _post_try_both(client: Any, base: str, json: dict, headers: dict) -> Any:
    """POST to underscore URL first, fall back to hyphen."""
    r = client.post(f"/{base.replace('-', '_')}/", json=json, headers=headers)
    if r.status_code == 404:
        r = client.post(f"/{base}/", json=json, headers=headers)
    return r


def test_shared_endpoint_no_auth(client: Any, auth_headers: Any, test_db: Any) -> None:
    """GET /shared/{token} — no auth required, returns branding + sheet."""
    # Create + share a sheet (requires auth)
    create = _post_try_both(client, "saved-sheets", json=_SHEET_PAYLOAD, headers=auth_headers)
    assert create.status_code == 201
    s_id = create.json()["id"]

    # Try underscore then hyphen for share endpoint
    share = client.post(f"/saved_sheets/{s_id}/share", headers=auth_headers)
    if share.status_code == 404:
        share = client.post(f"/saved-sheets/{s_id}/share", headers=auth_headers)
    assert share.status_code == 201
    token = share.json()["share_token"]

    # Now call the public endpoint WITHOUT auth headers
    response = client.get(f"/shared/{token}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "sheet" in data
    assert "branding" in data
    assert data["sheet"]["id"] == s_id
    assert "company_name" in data["branding"]
    logger.info("Shared payload includes branding for: %s", data["branding"].get("company_name"))


def test_shared_endpoint_invalid_token(client: Any) -> None:
    """Invalid token -> 404."""
    response = client.get("/shared/bogus-token-does-not-exist")
    assert response.status_code == 404
