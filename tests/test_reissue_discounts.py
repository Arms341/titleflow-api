"""
tests/test_reissue_discounts.py  v1.0.3
Locked template — JARVIS title_company gig.

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


def test_create_reissue_discount(client: Any, auth_headers: Any, test_db: Any) -> None:
    """POST /reissue-discounts/ -> 201."""
    rt_id = _create_rate_table(client, auth_headers)
    payload = {
        "rate_table_id": rt_id,
        "years_since_prior_policy": 5,
        "discount_pct": 30.0,
    }
    response = _post_try_both(client, "reissue-discounts", json=payload, headers=auth_headers)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    assert "id" in response.json()


def test_list_reissue_discounts(client: Any, auth_headers: Any) -> None:
    """GET /reissue-discounts/ -> 200."""
    response = _get_try_both(client, "/reissue-discounts/", headers=auth_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert isinstance(response.json(), list)


def test_update_reissue_discount(client: Any, auth_headers: Any, test_db: Any) -> None:
    """PUT /reissue-discounts/{id} -> 200."""
    rt_id = _create_rate_table(client, auth_headers)
    payload = {
        "rate_table_id": rt_id,
        "years_since_prior_policy": 5,
        "discount_pct": 30.0,
    }
    create = _post_try_both(client, "reissue-discounts", json=payload, headers=auth_headers)
    assert create.status_code == 201
    d_id = create.json()["id"]

    response = _put_try_both(client, f"/reissue-discounts/{d_id}", json={"discount_pct": 40.0},
                             headers=auth_headers)
    assert response.status_code == 200


def test_delete_reissue_discount(client: Any, auth_headers: Any, test_db: Any) -> None:
    """DELETE /reissue-discounts/{id} -> 200."""
    rt_id = _create_rate_table(client, auth_headers)
    payload = {
        "rate_table_id": rt_id,
        "years_since_prior_policy": 5,
        "discount_pct": 30.0,
    }
    create = _post_try_both(client, "reissue-discounts", json=payload, headers=auth_headers)
    d_id = create.json()["id"]

    delete_resp = _delete_try_both(client, f"/reissue-discounts/{d_id}", headers=auth_headers)
    assert delete_resp.status_code == 200
