from app.domain.fleet.validator import is_valid_fleet
from app.db.session import SessionLocal
from app.models.game import Game

from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app
client = TestClient(app)

def delete_game(session_id):
    db = SessionLocal()

    try:
        game = db.get(Game, UUID(session_id))

        if game is not None:
            db.delete(game)
            db.commit()
    finally:
        db.close()

def test_create_game_returns_201():
    response = client.post("/game")
    data = response.json()

    try:
        assert response.status_code == 201
    finally:
        if "session_id" in data:
            delete_game(data["session_id"])

def test_create_game_returns_expected_body():
    response = client.post("/game")
    data = response.json()

    try: 
        assert "session_id" in data
        assert "ships" in data
    finally:
        if "session_id" in data:
            delete_game(data["session_id"])

def test_create_game_returns_valid_uuid():
    response = client.post("/game")
    data = response.json()

    try:
        UUID(data["session_id"])
    finally:
        if "session_id" in data:
            delete_game(data["session_id"])

def test_create_game_returns_ships_list():
    response = client.post("/game")
    data = response.json()

    try:
        assert isinstance(data["ships"], list)
        assert len(data["ships"]) > 0
    finally:
        if "session_id" in data:
            delete_game(data["session_id"])

def test_create_game_returns_valid_fleet():
    response = client.post("/game")
    data = response.json()

    try:
        fleet = [
            ship["coordinates"]
            for ship in data["ships"]
        ]

        assert len(fleet) == 10
        assert sum(len(ship) for ship in fleet) == 20
        assert is_valid_fleet(fleet) is True
    finally:
        if "session_id" in data:
            delete_game(data["session_id"])

def test_create_game_persists_response_in_database():
    response = client.post("/game")
    data = response.json()

    try:
        db = SessionLocal()

        try:
            saved_game = db.get(Game, UUID(data["session_id"]))

            assert saved_game is not None
            assert saved_game.status == "active"
            assert saved_game.ships == data["ships"]
        finally:
            db.close()

    finally:
        if "session_id" in data:
            delete_game(data["session_id"])