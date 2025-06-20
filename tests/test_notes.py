import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def auth_token(client: TestClient):
    client.post("/register", json={"username": "testuser", "password": "1234"})
    response = client.post("/login", data={"username": "testuser", "password": "1234"})
    return response.json()["access_token"]

def test_create_note(client: TestClient, auth_token):
    response = client.post("/notes", json={"text": "My test note"}, headers={"Authorization": f"Bearer {auth_token}"})
    assert response.status_code == 200
    assert response.json()["text"] == "My test note"

def test_get_notes(client: TestClient, auth_token):
    response = client.get("/notes", headers={"Authorization": f"Bearer {auth_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_delete_note(client: TestClient, auth_token):
    note = client.post("/notes", json={"text": "to delete"}, headers={"Authorization": f"Bearer {auth_token}"}).json()
    note_id = note["id"]
    response = client.delete(f"/notes/{note_id}", headers={"Authorization": f"Bearer {auth_token}"})
    assert response.status_code == 200