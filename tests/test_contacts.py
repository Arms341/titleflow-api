"""
tests/test_contacts.py  v1.0.0
Locked template - JARVIS title_company gig.
Fields: first_name, last_name, email, phone, company_name, role, notes.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

_CONTACT_PAYLOAD = {
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane.doe@example.com",
    "phone": "806-555-1234",
    "company_name": "ABC Realty",
    "role": "buyer",
}

_CONTACT_UPDATE = {
    "first_name": "Janet",
    "phone": "806-555-9999",
    "role": "seller",
}


def test_create_contact(client: Any, auth_headers: Any) -> None:
    """POST /contacts/ -> 201."""
    response = client.post("/contacts/", json=_CONTACT_PAYLOAD, headers=auth_headers)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert "id" in data
    assert data.get("first_name") == "Jane"
    assert data.get("last_name") == "Doe"
    assert data.get("role") == "buyer"


def test_get_contact(client: Any, auth_headers: Any) -> None:
    """GET /contacts/{id} -> 200."""
    create = client.post("/contacts/", json=_CONTACT_PAYLOAD, headers=auth_headers)
    assert create.status_code == 201
    c_id = create.json()["id"]

    response = client.get(f"/contacts/{c_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == c_id
    assert "first_name" in data


def test_list_contacts(client: Any, auth_headers: Any) -> None:
    """GET /contacts/ -> 200 list."""
    response = client.get("/contacts/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_contact(client: Any, auth_headers: Any) -> None:
    """PUT /contacts/{id} -> 200."""
    create = client.post("/contacts/", json=_CONTACT_PAYLOAD, headers=auth_headers)
    c_id = create.json()["id"]

    response = client.put(f"/contacts/{c_id}", json=_CONTACT_UPDATE, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data.get("first_name") == "Janet"
    assert data.get("role") == "seller"


def test_delete_contact(client: Any, auth_headers: Any) -> None:
    """DELETE /contacts/{id} -> 200."""
    create = client.post("/contacts/", json=_CONTACT_PAYLOAD, headers=auth_headers)
    c_id = create.json()["id"]

    response = client.delete(f"/contacts/{c_id}", headers=auth_headers)
    assert response.status_code == 200

    # Verify deleted
    get_resp = client.get(f"/contacts/{c_id}", headers=auth_headers)
    assert get_resp.status_code == 404
