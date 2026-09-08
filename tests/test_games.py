from app.db.session import SessionLocal
from app.models.game import Game

from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app
client = TestClient(app)

def delete_game(game_id):
    db = SessionLocal()

    try:
        game = db.get(Game, UUID(game_id))

        if game is not None:
            db.delete(game)
            db.commit()
    finally:
        db.close()

def test_create_game_returns_201():
    response = client.post("/games")
    data = response.json()

    try:
        assert response.status_code == 201
    finally:
        if "game_id" in data:
            delete_game(data["game_id"])

def test_create_game_returns_expected_body():
    response = client.post("/games")
    data = response.json()

    try: 
        assert "game_id" in data
        assert "ships" in data
    finally:
        if "game_id" in data:
            delete_game(data["game_id"])

def test_create_game_returns_valid_uuid():
    response = client.post("/games")
    data = response.json()

    try:
        UUID(data["game_id"])
    finally:
        if "game_id" in data:
            delete_game(data["game_id"])

def test_create_game_returns_ships_list():
    response = client.post("/games")
    data = response.json()

    try:
        assert isinstance(data["ships"], list)
        assert len(data["ships"]) > 0
    finally:
        if "game_id" in data:
            delete_game(data["game_id"])