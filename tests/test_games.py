from app.domain.fleet.validator import is_valid_fleet
from app.db.session import SessionLocal
from app.models.game import Game

from uuid import UUID, uuid4

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

def test_opponent_shot_returns_miss_and_persists_shot():
    db = SessionLocal()

    game = Game(
        ships=[
            {"coordinates": ["A1", "A2"]},
        ]
    )

    try:
        db.add(game)
        db.commit()
        db.refresh(game)

        session_id = str(game.session_id)
    finally:
        db.close()

    try:
        response = client.post(
            f"/game/{session_id}/opponent-shot",
            json={"coordinate": "J10"},
        )
        assert response.status_code == 200
        assert response.json() == {"result": "miss"}

        db = SessionLocal()

        try:
            saved_game = db.get(Game, UUID(session_id))

            assert saved_game is not None
            assert saved_game.received_shots == ["J10"]
        finally: 
            db.close()

    finally: 
        delete_game(session_id)

def test_opponent_shot_returns_hit_then_killed():
    db = SessionLocal()

    game = Game(
        ships=[
            {"coordinates": ["A1", "A2"]},
        ]
    )

    try:
        db.add(game)
        db.commit()
        db.refresh(game)

        session_id = str(game.session_id)
    finally:
        db.close()

    try:
        first_response = client.post(
            f"/game/{session_id}/opponent-shot",
            json={"coordinate": "A1"},
        )

        second_response = client.post(
            f"/game/{session_id}/opponent-shot",
            json={"coordinate": "A2"},
        )

        assert first_response.status_code == 200
        assert first_response.json() == {"result": "hit"}

        assert second_response.status_code == 200
        assert second_response.json() == {"result": "killed"}

        db = SessionLocal()

        try:
            saved_game = db.get(Game, UUID(session_id))

            assert saved_game is not None
            assert saved_game.received_shots == ["A1", "A2"]
        finally:
            db.close()

    finally:
        delete_game(session_id)

def test_opponent_shot_returns_400_for_invalid_coordinate():
    response = client.post("/game")
    data = response.json()

    try:
        session_id = data["session_id"]

        response = client.post(
            f"/game/{session_id}/opponent-shot",
            json={"coordinate": "K1"},
        )

        assert response.status_code == 400
        assert response.json() == {
            "detail": "Invalid coordinate",
        }

    finally:
        if "session_id" in data:
            delete_game(data["session_id"])

def test_opponent_shot_returns_404_for_unknown_session():
    session_id = uuid4()

    response = client.post(
        f"/game/{session_id}/opponent-shot",
        json={"coordinate": "A1"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Game session not found",
    }

def test_opponent_shot_returns_410_for_closed_session():
    db = SessionLocal()

    game = Game(
        ships=[
            {"coordinates": ["A1", "A2"]},
        ],
        status="closed",
    )

    try:
        db.add(game)
        db.commit()
        db.refresh(game)

        session_id = str(game.session_id)
    finally:
        db.close()

    try:
        response = client.post(
            f"/game/{session_id}/opponent-shot",
            json={"coordinate": "A1"},
        )

        assert response.status_code == 410
        assert response.json() == {
            "detail": "Game session is closed",
        }

    finally:
        delete_game(session_id)