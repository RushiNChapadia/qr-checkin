from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get_token(email: str) -> str:
    client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    assert r.status_code == 200
    return r.json()["access_token"]


def create_event(token: str) -> str:
    r = client.post(
        "/api/v1/events",
        json={"name": "Checkin Event", "venue": None, "start_time": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    return r.json()["id"]


def create_attendee(token: str, event_id: str) -> dict:
    r = client.post(
        f"/api/v1/events/{event_id}/attendees",
        json={"full_name": "Alice", "email": "alice@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    return r.json()


def test_checkin_idempotent_and_stats():
    token = get_token("checkin_owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    event_id = create_event(token)
    attendee = create_attendee(token, event_id)
    qr_token = attendee["qr_token"]

    # stats before
    s1 = client.get(f"/api/v1/events/{event_id}/stats", headers=headers)
    assert s1.status_code == 200
    assert s1.json()["checked_in"] == 0

    # first checkin
    c1 = client.post("/api/v1/checkin", json={"qr_token": qr_token, "device_id": "ipad-1"}, headers=headers)
    assert c1.status_code == 200
    assert c1.json()["already_checked_in"] is False
    assert c1.json()["full_name"] == "Alice"

    # second checkin (idempotent)
    c2 = client.post("/api/v1/checkin", json={"qr_token": qr_token, "device_id": "ipad-1"}, headers=headers)
    assert c2.status_code == 200
    assert c2.json()["already_checked_in"] is True

    # stats after
    s2 = client.get(f"/api/v1/events/{event_id}/stats", headers=headers)
    assert s2.status_code == 200
    assert s2.json()["checked_in"] == 1
    assert s2.json()["not_checked_in"] >= 0


def test_checkin_invalid_token():
    token = get_token("checkin_invalid@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post("/api/v1/checkin", json={"qr_token": "this-is-not-a-real-token"}, headers=headers)
    assert r.status_code == 404
