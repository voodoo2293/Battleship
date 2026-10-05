from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
from uuid import UUID
from threading import Barrier

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

def test_parallel_close_same_session_allows_only_one_success():
    response = client.post("/game")

    assert response.status_code == 201

    session_id = response.json()["session_id"]

    barrier = Barrier(2)

    def close_session():
        barrier.wait()

        response = client.post(
            f"/game/{session_id}/close"
        )

        return response.status_code

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(close_session)
                for _ in range(2)
            ]

            status_codes = [
                future.result()
                for future in futures
            ]

        assert sorted(status_codes) == [200, 400]

        db = SessionLocal()

        try:
            game = db.get(
                Game,
                UUID(session_id),
            )

            assert game is not None
            assert game.status == "closed"

        finally:
            db.close()

    finally:
        delete_game(session_id)

def test_parallel_shot_same_session_allows_only_one_pending_shot():
    response = client.post("/game")

    assert response.status_code == 201

    session_id = response.json()["session_id"]

    barrier = Barrier(2)

    def make_shot():
        barrier.wait()

        response = client.post(
            f"/game/{session_id}/shot"
        )

        return response.status_code

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(make_shot)
                for _ in range(2)
            ]

            status_codes = [
                future.result()
                for future in futures
            ]

        assert sorted(status_codes) == [200, 409]

        db = SessionLocal()

        try:
            game = db.get(
                Game,
                UUID(session_id),
            )

            assert game is not None
            assert game.outgoing_shots == [
                {
                    "coordinate": "A1",
                    "result": None,
                }
            ]

        finally:
            db.close()

    finally:
        delete_game(session_id)

def test_parallel_shot_result_same_session_allows_only_one_result():
    response = client.post("/game")

    assert response.status_code == 201

    session_id = response.json()["session_id"]

    shot_response = client.post(
        f"/game/{session_id}/shot"
    )

    assert shot_response.status_code == 200

    barrier = Barrier(2)

    def send_result(result):
        barrier.wait()

        response = client.post(
            f"/game/{session_id}/shot/result",
            json={"result": result},
        )

        return response.status_code

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(send_result, "hit"),
                executor.submit(send_result, "miss"),
            ]

            status_codes = [
                future.result()
                for future in futures
            ]

        assert sorted(status_codes) == [200, 409]

        db = SessionLocal()

        try:
            game = db.get(
                Game,
                UUID(session_id),
            )

            assert game is not None
            assert len(game.outgoing_shots) == 1
            assert game.outgoing_shots[0]["coordinate"] == "A1"
            assert game.outgoing_shots[0]["result"] in {
                "hit",
                "miss",
            }

        finally:
            db.close()

    finally:
        delete_game(session_id)

def test_parallel_opponent_shots_same_session_keep_both_shots():
    response = client.post("/game")

    assert response.status_code == 201

    session_id = response.json()["session_id"]

    barrier = Barrier(2)

    def send_shot(coordinate):
        barrier.wait()

        response = client.post(
            f"/game/{session_id}/opponent-shot",
            json={"coordinate": coordinate},
        )

        return response.status_code

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(send_shot, "A1"),
                executor.submit(send_shot, "J10"),
            ]

            status_codes = [
                future.result()
                for future in futures
            ]

        assert status_codes == [200, 200]

        db = SessionLocal()

        try:
            game = db.get(
                Game,
                UUID(session_id),
            )

            assert game is not None
            assert sorted(game.received_shots) == [
                "A1",
                "J10",
            ]

        finally:
            db.close()

    finally:
        delete_game(session_id)

def test_parallel_close_and_shot_same_session_keep_state_consistent():
    response = client.post("/game")
    
    assert response.status_code == 201

    session_id = response.json()["session_id"]

    barrier = Barrier(2)

    def close_session():
        barrier.wait()

        response = client.post(
            f"/game/{session_id}/close"
        )

        return "close", response.status_code

    def make_shot():
        barrier.wait()

        response = client.post(
            f"/game/{session_id}/shot"
        )

        return "shot", response.status_code

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(close_session),
                executor.submit(make_shot),
            ]

            results = dict(
                future.result()
                for future in futures
            )

        assert results["close"] == 200
        assert results["shot"] in {200, 410}

        db = SessionLocal()

        try:
            game = db.get(
                Game,
                UUID(session_id),
            )

            assert game is not None
            assert game.status == "closed"

            if results["shot"] == 200:
                assert game.outgoing_shots == [
                    {
                        "coordinate": "A1",
                        "result": None,
                    }
                ]
            else:
                assert game.outgoing_shots == []

        finally:
            db.close()

    finally:
        delete_game(session_id)
