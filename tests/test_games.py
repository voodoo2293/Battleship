from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app
client = TestClient(app)

def test_create_game_returns_201():
    response = client.post("/games")
    assert response.status_code == 201

def test_create_game_returns_expected_body():
    response = client.post("/games")

    data = response.json()

    assert "session_id" in data
    assert "ships" in data

def test_create_game_returns_valid_uuid():
    response = client.post("/games")

    data = response.json()

    UUID(data["session_id"])

def test_create_game_returns_ship_list():
    response = client.post("/games")

    data = response.json()

    assert isinstance(data["ships"], list)
    assert len(data["ships"]) > 0