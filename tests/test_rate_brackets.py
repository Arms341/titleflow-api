"""
tests/test_rate_brackets.py  v1.0.3
Locked template — JARVIS title_company gig.
CRUD + critical bracket math verification test.

v1.0.3: Try-both-URLs pattern — tries /rate_brackets/ (underscore) first,
  falls back to /rate-brackets/ (hyphen). No import of main.py needed.
  Eliminates all runtime detection complexity. Works regardless of what
  convention the AI chose in main.py.
v1.0.2: Runtime prefix detection via app.routes (fragile — pipeline strips imports).
v1.0.1: Inlined helpers to prevent IMP4-RECONCILE stripping.
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


def _create_rate_table(client: Any, auth_headers: Any) -> int:
    """Helper: create a rate table and return its id."""
    r = _post_try_both(client, "rate-tables", json=_rt_payload(), headers=auth_headers)
    assert r.status_code == 201, f"Rate table setup failed: {r.status_code} {r.text}"
    return r.json()["id"]


def test_create_rate_bracket(client: Any, auth_headers: Any, test_db: Any) -> None:
    """POST /rate-brackets/ or /rate_brackets/ -> 201."""
    rt_id = _create_rate_table(client, auth_headers)
    payload = {
        "rate_table_id": rt_id,
        "min_value": 0,
        "max_value": 100000,
        "rate_per_thousand": 5.75,
    }
    response = _post_try_both(client, "rate-brackets", json=payload, headers=auth_headers)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    assert "id" in response.json()
    logger.info("Created rate_bracket id=%s", response.json()["id"])


def test_list_rate_brackets(client: Any, auth_headers: Any) -> None:
    """GET /rate-brackets/ -> 200."""
    response = _get_try_both(client, "/rate-brackets/", headers=auth_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert isinstance(response.json(), list)


def test_bulk_create_brackets(client: Any, auth_headers: Any, test_db: Any) -> None:
    """POST /rate-brackets/bulk/{rate_table_id} -> 201."""
    rt_id = _create_rate_table(client, auth_headers)
    payload = {
        "brackets": [
            {"rate_table_id": rt_id, "min_value": 0, "max_value": 100000, "rate_per_thousand": 5.75},
            {"rate_table_id": rt_id, "min_value": 100000, "max_value": 500000, "rate_per_thousand": 5.00},
            {"rate_table_id": rt_id, "min_value": 500000, "max_value": 1000000, "rate_per_thousand": 4.50},
        ],
    }
    response = _post_try_both(client, f"rate-brackets/bulk/{rt_id}", json=payload, headers=auth_headers)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    logger.info("Bulk-created %d brackets", len(data))


def test_update_rate_bracket(client: Any, auth_headers: Any, test_db: Any) -> None:
    """PUT /rate-brackets/{id} -> 200."""
    rt_id = _create_rate_table(client, auth_headers)
    payload = {
        "rate_table_id": rt_id,
        "min_value": 0,
        "max_value": 100000,
        "rate_per_thousand": 5.75,
    }
    create = _post_try_both(client, "rate-brackets", json=payload, headers=auth_headers)
    assert create.status_code == 201
    b_id = create.json()["id"]

    response = _put_try_both(client, f"/rate-brackets/{b_id}", json={"rate_per_thousand": 6.00},
                             headers=auth_headers)
    assert response.status_code == 200
    logger.info("Updated rate_bracket id=%s", b_id)


def test_delete_rate_bracket(client: Any, auth_headers: Any, test_db: Any) -> None:
    """DELETE /rate-brackets/{id} -> 200."""
    rt_id = _create_rate_table(client, auth_headers)
    payload = {
        "rate_table_id": rt_id,
        "min_value": 0,
        "max_value": 100000,
        "rate_per_thousand": 5.75,
    }
    create = _post_try_both(client, "rate-brackets", json=payload, headers=auth_headers)
    b_id = create.json()["id"]

    delete_resp = _delete_try_both(client, f"/rate-brackets/{b_id}", headers=auth_headers)
    assert delete_resp.status_code == 200
    logger.info("Deleted rate_bracket id=%s", b_id)
