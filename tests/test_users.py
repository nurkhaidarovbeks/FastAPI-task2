import pytest
from fastapi.testclient import TestClient

def test_users_me_success(client: TestClient):
    client.post("/register", json={"username": "testuser", "password": "1234"})
    login = client.post("/login", data={"username": "testuser", "password": "1234"})
    token = login.json()["access_token"]
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

def test_users_me_unauthorized(client: TestClient):
    response = client.get("/users/me")
    assert response.status_code == 401