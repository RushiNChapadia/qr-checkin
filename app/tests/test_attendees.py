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
        json={"name": "Event A", "venue": "LA", "start_time": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    return r.json()["id"]


def test_attendee_create_list_get_qr():
    token = get_token("attendee_owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    event_id = create_event(token)

    # create attendee
    r1 = client.post(
        f"/api/v1/events/{event_id}/attendees",
        json={"full_name": "John Doe", "email": "john@example.com"},
        headers=headers,
    )
    assert r1.status_code == 201
    attendee = r1.json()
    attendee_id = attendee["id"]
    assert attendee["qr_token"]
    assert attendee["checked_in_at"] is None

    # list attendees
    r2 = client.get(f"/api/v1/events/{event_id}/attendees?limit=50&offset=0", headers=headers)
    assert r2.status_code == 200
    data = r2.json()
    assert data["total"] >= 1

    # get attendee
    r3 = client.get(f"/api/v1/events/{event_id}/attendees/{attendee_id}", headers=headers)
    assert r3.status_code == 200
    assert r3.json()["id"] == attendee_id

    # get qr payload
    r4 = client.get(f"/api/v1/events/{event_id}/attendees/{attendee_id}/qr", headers=headers)
    assert r4.status_code == 200
    qr = r4.json()
    assert qr["qr_token"]
    assert qr["payload"] == qr["qr_token"]


def test_attendees_forbidden_other_user():
    token_a = get_token("att_a@example.com")
    token_b = get_token("att_b@example.com")

    event_id = create_event(token_a)

    # user B tries to list attendees for user A's event
    r = client.get(
        f"/api/v1/events/{event_id}/attendees",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r.status_code == 403
