import pytest
from fastapi.testclient import TestClient


def test_register_user(client: TestClient):
    response = client.post("/register", json={"username": "testuser", "password": "password"})
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"


def test_register_duplicate_user(client: TestClient):
    response = client.post("/register", json={"username": "testuser", "password": "password"})
    assert response.status_code == 400


def test_login_success(client: TestClient):
    client.post("/register", json={"username": "testuser", "password": "password"})

    # login: используем data, не json
    response = client.post("/login", data={"username": "testuser", "password": "password"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_fall(client: TestClient):
    response = client.post("/login", data={"username": "wrong", "password": "wrong"})
    assert response.status_code == 401