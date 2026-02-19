from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_and_login():
    # register
    r = client.post("/api/v1/auth/register", json={"email": "test@example.com", "password": "Password123!"})
    assert r.status_code in (201, 409)  # allow reruns

    # login
    r2 = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "Password123!"})
    assert r2.status_code == 200
    data = r2.json()
    assert "access_token" in data
