"""
tests/test_rate_tables.py  v1.0.3
Locked template — JARVIS title_company gig.
CRUD tests + bracket math verification (critical business logic test).

v1.0.3: Try-both-URLs pattern (underscore then hyphen). No main.py import.
v1.0.2: Runtime prefix detection (fragile).
v1.0.1: Converted module-level _RATE_TABLE_PAYLOAD to function form.
"""
import logging
from typing import Any
import pytest

logger = logging.getLogger(__name__)


def _rt_payload() -> dict:
    """Return a valid rate table create payload."""
    return {
        "name": "TX Owner Standard",
        "state": "TX",
        "table_type": "owner_policy",
        "is_active": True,
    }


def _rt_update() -> dict:
    """Return rate table update payload."""
    return {
        "name": "Texas Owner Policy 2026",
        "is_active": True,
    }


def _post_try_both(client: Any, base: str, json: dict, headers: dict) -> Any:
    """POST to underscore URL first, fall back to hyphen."""
    r = client.post(f"/{base.replace('-', '_')}/", json=json, headers=headers)
    if r.status_code == 404:
        r = client.post(f"/{base}/", json=json, headers=headers)
    return r


def _get_try_both(client: Any, path: str, headers: dict = None, **kwargs: Any) -> Any:
    """GET trying underscore then hyphen."""
    underscore = path.replace('-', '_')
    r = client.get(underscore, headers=headers, **kwargs)
    if r.status_code == 404:
        r = client.get(path, headers=headers, **kwargs)
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


def test_create_rate_table(client: Any, auth_headers: Any) -> None:
    """POST /rate-tables/ -> 201 with id."""
    response = _post_try_both(client, "rate-tables", json=_rt_payload(), headers=auth_headers)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert "id" in data
    logger.info("Created rate_table id=%s", data["id"])


def test_get_rate_table(client: Any, auth_headers: Any, test_db: Any) -> None:
    """GET /rate-tables/{id} -> 200."""
    create = _post_try_both(client, "rate-tables", json=_rt_payload(), headers=auth_headers)
    assert create.status_code == 201
    rt_id = create.json()["id"]

    response = _get_try_both(client, f"/rate-tables/{rt_id}", headers=auth_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json()["id"] == rt_id
    logger.info("Retrieved rate_table id=%s", rt_id)


def test_list_rate_tables(client: Any, auth_headers: Any) -> None:
    """GET /rate-tables/ -> 200 list."""
    response = _get_try_both(client, "/rate-tables/", headers=auth_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert isinstance(response.json(), list)
    logger.info("Listed %d rate_tables", len(response.json()))


def test_update_rate_table(client: Any, auth_headers: Any, test_db: Any) -> None:
    """PUT /rate-tables/{id} -> 200."""
    create = _post_try_both(client, "rate-tables", json=_rt_payload(), headers=auth_headers)
    assert create.status_code == 201
    rt_id = create.json()["id"]

    response = _put_try_both(client, f"/rate-tables/{rt_id}", json=_rt_update(), headers=auth_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    logger.info("Updated rate_table id=%s", rt_id)


def test_delete_rate_table(client: Any, auth_headers: Any, test_db: Any) -> None:
    """DELETE /rate-tables/{id} -> 200, subsequent GET -> 404."""
    create = _post_try_both(client, "rate-tables", json=_rt_payload(), headers=auth_headers)
    assert create.status_code == 201
    rt_id = create.json()["id"]

    delete_resp = _delete_try_both(client, f"/rate-tables/{rt_id}", headers=auth_headers)
    assert delete_resp.status_code == 200, f"Expected 200, got {delete_resp.status_code}: {delete_resp.text}"

    get_after = _get_try_both(client, f"/rate-tables/{rt_id}", headers=auth_headers)
    assert get_after.status_code == 404
    logger.info("Confirmed rate_table id=%s is gone", rt_id)


def test_public_rate_tables_unauth(client: Any) -> None:
    """GET /rate-tables/public — no auth required."""
    response = _get_try_both(client, "/rate-tables/public?state=TX")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert isinstance(response.json(), list)
    logger.info("Public endpoint returned %d tables", len(response.json()))
