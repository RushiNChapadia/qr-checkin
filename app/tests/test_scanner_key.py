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
        json={"name": "Scanner Event", "venue": None, "start_time": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    return r.json()["id"]


def create_attendee(token: str, event_id: str) -> str:
    r = client.post(
        f"/api/v1/events/{event_id}/attendees",
        json={"full_name": "Bob", "email": "bob@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    return r.json()["qr_token"]


def get_scanner_key(token: str, event_id: str) -> str:
    r = client.get(
        f"/api/v1/events/{event_id}/scanner-key",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    return r.json()["scanner_key"]


def rotate_scanner_key(token: str, event_id: str) -> str:
    r = client.post(
        f"/api/v1/events/{event_id}/scanner-key/rotate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    return r.json()["scanner_key"]


def test_checkin_with_scanner_key_no_jwt():
    owner_token = get_token("scanner_owner@example.com")
    event_id = create_event(owner_token)
    qr_token = create_attendee(owner_token, event_id)
    scanner_key = get_scanner_key(owner_token, event_id)

    # No Authorization header; only scanner key
    r = client.post(
        "/api/v1/checkin",
        json={"qr_token": qr_token, "device_id": "ipad-1"},
        headers={"X-Scanner-Key": scanner_key},
    )
    assert r.status_code == 200
    assert r.json()["already_checked_in"] is False


def test_old_scanner_key_invalid_after_rotate():
    owner_token = get_token("scanner_rotate_owner@example.com")
    event_id = create_event(owner_token)
    qr_token = create_attendee(owner_token, event_id)

    old_key = get_scanner_key(owner_token, event_id)
    new_key = rotate_scanner_key(owner_token, event_id)
    assert old_key != new_key

    # old key should fail
    r1 = client.post(
        "/api/v1/checkin",
        json={"qr_token": qr_token},
        headers={"X-Scanner-Key": old_key},
    )
    assert r1.status_code == 401

    # new key should work
    r2 = client.post(
        "/api/v1/checkin",
        json={"qr_token": qr_token},
        headers={"X-Scanner-Key": new_key},
    )
    assert r2.status_code == 200
