from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
from uuid import UUID

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.game import Game

client = TestClient(app)

def delete_game(session_id: str):
    db = SessionLocal()

    try:
        game = db.get(Game, UUID(session_id))

        if game is not None:
            db.delete(game)
            db.commit()
    finally:
        db.close()

def test_two_sessions_keep_state_isolated():
    first_response = client.post("/game")
    second_response = client.post("/game")

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_session_id = first_response.json()["session_id"]
    second_session_id = second_response.json()["session_id"]

    assert first_session_id != second_session_id

    try:
        first_shot = client.post(
            f"/game/{first_session_id}/opponent-shot",
            json={"coordinate": "A1"},
        )

        second_shot = client.post(
            f"/game/{second_session_id}/opponent-shot",
            json={"coordinate": "J10"},
        )

        assert first_shot.status_code == 200
        assert second_shot.status_code == 200

        close_response = client.post(
            f"/game/{first_session_id}/close"
        )

        assert close_response.status_code == 200

        db = SessionLocal()

        try:
            first_game = db.get(
                Game,
                UUID(first_session_id),
            )
            second_game = db.get(
                Game,
                UUID(second_session_id),
            )

            assert first_game is not None
            assert second_game is not None

            assert first_game.received_shots == ["A1"]
            assert second_game.received_shots == ["J10"]

            assert first_game.status == "closed"
            assert second_game.status == "active"

        finally:
            db.close()

    finally:
        delete_game(first_session_id)
        delete_game(second_session_id)

def test_two_sessions_keep_outgoing_shots_isolated():
    first_response = client.post("/game")
    second_response = client.post("/game")

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_session_id = first_response.json()["session_id"]
    second_session_id = second_response.json()["session_id"]

    try:
        first_shot = client.post(
            f"/game/{first_session_id}/shot"
        )
        second_shot = client.post(
            f"/game/{second_session_id}/shot"
        )

        assert first_shot.status_code == 200
        assert second_shot.status_code == 200

        assert first_shot.json()["coordinate"] == "A1"
        assert second_shot.json()["coordinate"] == "A1"

        first_result = client.post(
            f"/game/{first_session_id}/shot/result",
            json={"result": "hit"},
        )
        second_result = client.post(
            f"/game/{second_session_id}/shot/result",
            json={"result": "miss"},
        )

        assert first_result.status_code == 200
        assert second_result.status_code == 200

        first_next_shot = client.post(
            f"/game/{first_session_id}/shot"
        )
        second_next_shot = client.post(
            f"/game/{second_session_id}/shot"
        )

        assert first_next_shot.status_code == 200
        assert second_next_shot.status_code == 200

        assert first_next_shot.json()["coordinate"] == "B1"
        assert second_next_shot.json()["coordinate"] == "A2"

        db = SessionLocal()

        try:
            first_game = db.get(
                Game,
                UUID(first_session_id),
            )
            second_game = db.get(
                Game,
                UUID(second_session_id),
            )

            assert first_game.outgoing_shots == [
                {
                    "coordinate": "A1",
                    "result": "hit",
                },
                {
                    "coordinate": "B1",
                    "result": None,
                },
            ]

            assert second_game.outgoing_shots == [
                {
                    "coordinate": "A1",
                    "result": "miss",
                },
                {
                    "coordinate": "A2",
                    "result": None,
                },
            ]

        finally:
            db.close()

    finally:
        delete_game(first_session_id)
        delete_game(second_session_id)

def test_parallel_opponent_shots_keep_sessions_isolated():
    session_ids = []

    coordinates = [
        "A1",
        "B2",
        "C3",
        "D4",
        "E5",
        "F6",
        "G7",
        "H8",
    ]

    try:
        for _ in coordinates:
            response = client.post("/game")

            assert response.status_code == 201

            session_ids.append(
                response.json()["session_id"]
            )

        def send_shot(session_id, coordinate):
            response = client.post(
                f"/game/{session_id}/opponent-shot",
                json={"coordinate": coordinate},
            )

            return response.status_code

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(
                    send_shot,
                    session_id,
                    coordinate,
                )
                for session_id, coordinate
                in zip(session_ids, coordinates)
            ]

            status_codes = [
                future.result()
                for future in futures
            ]

        assert status_codes == [200] * 8

        db = SessionLocal()

        try:
            for session_id, coordinate in zip(
                session_ids,
                coordinates,
            ):
                game = db.get(
                    Game,
                    UUID(session_id),
                )

                assert game is not None
                assert game.received_shots == [
                    coordinate
                ]

        finally:
            db.close()

    finally:
        for session_id in session_ids:
            delete_game(session_id)

def test_parallel_requests_finish_under_one_second():
    session_ids = []

    coordinates = [
        "A1",
        "B2",
        "C3",
        "D4",
        "E5",
        "F6",
        "G7",
        "H8",
    ]

    try:
        for _ in coordinates:
            response = client.post("/game")

            assert response.status_code == 201

            session_ids.append(
                response.json()["session_id"]
            )

        def send_timed_shot(session_id, coordinate):
            started_at = perf_counter()

            response = client.post(
                f"/game/{session_id}/opponent-shot",
                json={"coordinate": coordinate},
            )

            elapsed = perf_counter() - started_at

            return response.status_code, elapsed

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(
                    send_timed_shot,
                    session_id,
                    coordinate,
                )
                for session_id, coordinate
                in zip(session_ids, coordinates)
            ]

            results = [
                future.result()
                for future in futures
            ]

        for status_code, elapsed in results:
            assert status_code == 200
            assert elapsed < 1.0, (
                f"Response took {elapsed:.3f} seconds"
            )

    finally:
        for session_id in session_ids:
            delete_game(session_id)
