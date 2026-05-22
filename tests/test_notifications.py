"""
tests/test_notifications.py  v1.0.0
Locked template — JARVIS title_company gig.
Fields: title, description, status. NEVER message/content/body/type.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

_NOTIFICATION_PAYLOAD = {
    "title": "Test Notification",
    "description": "This is a test notification",
    "status": "unread",
}

_NOTIFICATION_UPDATE = {
    "title": "Updated Notification",
    "status": "read",
}


def test_create_notification(client: Any, auth_headers: Any) -> None:
    """POST /notifications/ → 201."""
    response = client.post("/notifications/", json=_NOTIFICATION_PAYLOAD, headers=auth_headers)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert "id" in data
    assert data.get("title") == "Test Notification"
    assert data.get("status") == "unread"


def test_get_notification(client: Any, auth_headers: Any) -> None:
    """GET /notifications/{id} → 200."""
    create = client.post("/notifications/", json=_NOTIFICATION_PAYLOAD, headers=auth_headers)
    assert create.status_code == 201
    n_id = create.json()["id"]

    response = client.get(f"/notifications/{n_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == n_id
    assert "title" in data


def test_list_notifications(client: Any, auth_headers: Any) -> None:
    """GET /notifications/ → 200 list."""
    response = client.get("/notifications/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_notification(client: Any, auth_headers: Any) -> None:
    """PUT /notifications/{id} → 200."""
    create = client.post("/notifications/", json=_NOTIFICATION_PAYLOAD, headers=auth_headers)
    n_id = create.json()["id"]

    response = client.put(f"/notifications/{n_id}", json=_NOTIFICATION_UPDATE, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "read"


def test_delete_notification(client: Any, auth_headers: Any) -> None:
    """DELETE /notifications/{id} → 200."""
    create = client.post("/notifications/", json=_NOTIFICATION_PAYLOAD, headers=auth_headers)
    n_id = create.json()["id"]

    response = client.delete(f"/notifications/{n_id}", headers=auth_headers)
    assert response.status_code == 200

    # Verify deleted
    get_resp = client.get(f"/notifications/{n_id}", headers=auth_headers)
    assert get_resp.status_code == 404
