"""
tests/test_saved_sheets.py  v1.0.3
Locked template — JARVIS title_company gig.

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
    "input_data": {"sale_price": "400000.00", "loan_balance": "250000.00"},
    "output_data": {"net_proceeds": "125000.00"},
}

_SHEET_UPDATE = {
    "property_address": "456 Oak Ave",
    "is_shared": True,
}


def _post_try_both(client: Any, base: str, json: dict, headers: dict) -> Any:
    """POST to underscore URL first, fall back to hyphen."""
    r = client.post(f"/{base.replace('-', '_')}/", json=json, headers=headers)
    if r.status_code == 404:
        r = client.post(f"/{base}/", json=json, headers=headers)
    return r


def _get_try_both(client: Any, path: str, headers: dict = None) -> Any:
    """GET trying underscore then hyphen."""
    underscore = path.replace('-', '_')
    r = client.get(underscore, headers=headers)
    if r.status_code == 404:
        r = client.get(path, headers=headers)
    return r


def _put_try_both(client: Any, path: str, json: dict, headers: dict) -> Any:
    """PUT trying underscore then hyphen."""
    underscore = path.replace('-', '_')
    r = client.put(underscore, json=json, headers=headers)
    if r.status_code == 404:
        r = client.put(path, json=json, headers=headers)
    return r


def _delete_try_both(client: Any, path: str, headers: dict) -> Any:
    """DELETE trying underscore then hyphen."""
    underscore = path.replace('-', '_')
    r = client.delete(underscore, headers=headers)
    if r.status_code == 404:
        r = client.delete(path, headers=headers)
    return r


def test_create_saved_sheet(client: Any, auth_headers: Any) -> None:
    """POST /saved-sheets/ -> 201."""
    response = _post_try_both(client, "saved-sheets", json=_SHEET_PAYLOAD, headers=auth_headers)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert "id" in data


def test_get_saved_sheet(client: Any, auth_headers: Any, test_db: Any) -> None:
    """GET /saved-sheets/{id} -> 200."""
    create = _post_try_both(client, "saved-sheets", json=_SHEET_PAYLOAD, headers=auth_headers)
    assert create.status_code == 201
    s_id = create.json()["id"]

    response = _get_try_both(client, f"/saved-sheets/{s_id}", headers=auth_headers)
    assert response.status_code == 200


def test_list_saved_sheets(client: Any, auth_headers: Any) -> None:
    """GET /saved-sheets/ -> 200."""
    response = _get_try_both(client, "/saved-sheets/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_saved_sheet(client: Any, auth_headers: Any, test_db: Any) -> None:
    """PUT /saved-sheets/{id} -> 200."""
    create = _post_try_both(client, "saved-sheets", json=_SHEET_PAYLOAD, headers=auth_headers)
    s_id = create.json()["id"]

    response = _put_try_both(client, f"/saved-sheets/{s_id}", json=_SHEET_UPDATE, headers=auth_headers)
    assert response.status_code == 200


def test_delete_saved_sheet(client: Any, auth_headers: Any, test_db: Any) -> None:
    """DELETE /saved-sheets/{id} -> 200."""
    create = _post_try_both(client, "saved-sheets", json=_SHEET_PAYLOAD, headers=auth_headers)
    s_id = create.json()["id"]

    delete = _delete_try_both(client, f"/saved-sheets/{s_id}", headers=auth_headers)
    assert delete.status_code == 200


def test_share_saved_sheet(client: Any, auth_headers: Any, test_db: Any) -> None:
    """POST /saved-sheets/{id}/share -> 201 with token + url."""
    create = _post_try_both(client, "saved-sheets", json=_SHEET_PAYLOAD, headers=auth_headers)
    s_id = create.json()["id"]

    # Try underscore then hyphen for the share endpoint
    share = client.post(f"/saved_sheets/{s_id}/share", headers=auth_headers)
    if share.status_code == 404:
        share = client.post(f"/saved-sheets/{s_id}/share", headers=auth_headers)
    assert share.status_code == 201, f"Expected 201, got {share.status_code}: {share.text}"
    data = share.json()
    assert "share_token" in data
    assert "share_url" in data
    logger.info("Generated share token: %s", data["share_token"])
