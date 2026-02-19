from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get_token(email: str) -> str:
    client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_events_crud_minimal():
    token = get_token("events_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # create event
    r1 = client.post(
        "/api/v1/events",
        json={"name": "My Event", "venue": "Anaheim", "start_time": None},
        headers=headers,
    )
    assert r1.status_code == 201
    event = r1.json()
    assert event["name"] == "My Event"
    event_id = event["id"]

    # list events
    r2 = client.get("/api/v1/events?limit=20&offset=0", headers=headers)
    assert r2.status_code == 200
    data = r2.json()
    assert "items" in data and data["total"] >= 1

    # get event
    r3 = client.get(f"/api/v1/events/{event_id}", headers=headers)
    assert r3.status_code == 200
    assert r3.json()["id"] == event_id


def test_event_forbidden_for_other_user():
    token_a = get_token("owner_a@example.com")
    token_b = get_token("owner_b@example.com")

    # owner A creates event
    r1 = client.post(
        "/api/v1/events",
        json={"name": "Private Event", "venue": None, "start_time": None},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r1.status_code == 201
    event_id = r1.json()["id"]

    # owner B tries to access it
    r2 = client.get(
        f"/api/v1/events/{event_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r2.status_code == 403
