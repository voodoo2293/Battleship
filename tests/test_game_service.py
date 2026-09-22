from app.db.session import SessionLocal
from app.domain.fleet.validator import is_valid_fleet
from app.models.game import Game
from app.services.game import (
    NoPendingShotError,
    ShotPendingError,
    create_game,
    create_shot,
    process_opponent_shot,
    process_shot_result,
)

def test_create_game_persists_game_in_database():
    db = SessionLocal()

    try:
        game = create_game(db)
        session_id = game.session_id
    finally:
        db.close()

    db = SessionLocal()

    try:
        saved_game = db.get(Game, session_id)

        assert saved_game is not None
        assert saved_game.status == "active"
        assert len(saved_game.ships) == 10

        fleet = [
            ship["coordinates"]
            for ship in saved_game.ships
        ]

        assert sum(len(ship) for ship in fleet) == 20
        assert is_valid_fleet(fleet) is True

    finally:
        saved_game = db.get(Game, session_id)

        if saved_game is not None:
            db.delete(saved_game)
            db.commit()

        db.close()

def test_process_opponent_shot_persists_miss():
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

        session_id = game.session_id

        result = process_opponent_shot(
            db=db,
            session_id=session_id,
            coordinate="J10",
        )

        assert result == "miss"

    finally:
        db.close()

    db = SessionLocal()

    try:
        saved_game = db.get(Game, session_id)

        assert saved_game is not None
        assert saved_game.received_shots == ["J10"]

    finally:
        saved_game = db.get(Game, session_id)

        if saved_game is not None:
            db.delete(saved_game)
            db.commit()

        db.close()

def test_process_opponent_shot_returns_killed_on_last_deck():
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

        session_id = game.session_id

        first_result = process_opponent_shot(
            db=db,
            session_id=session_id,
            coordinate="A1",
        )

        second_result = process_opponent_shot(
            db=db,
            session_id=session_id,
            coordinate="A2"
        )

        assert first_result == "hit"
        assert second_result == "killed"

    finally:
        db.close()

    db = SessionLocal()

    try:
        saved_game = db.get(Game, session_id)

        assert saved_game is not None
        assert saved_game.received_shots == ["A1", "A2"]

    finally:
        saved_game = db.get(Game, session_id)

        if saved_game is not None:
            db.delete(saved_game)
            db.commit()

        db.close()

def test_process_opponent_shot_allows_repeated_shot():
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

        session_id = game.session_id

        first_result = process_opponent_shot(
            db=db,
            session_id=session_id,
            coordinate="A1",
        )

        repeated_result = process_opponent_shot(
            db=db,
            session_id=session_id,
            coordinate="A1",
        )

        assert first_result == "hit"
        assert repeated_result == "hit"

    finally:
        db.close()

    db = SessionLocal()

    try:
        saved_game = db.get(Game, session_id)

        assert saved_game is not None
        assert saved_game.received_shots == ["A1", "A1"]

    finally: 
        saved_game = db.get(Game, session_id)

        if saved_game is not None:
            db.delete(saved_game)
            db.commit()

        db.close()

def test_create_shot_persists_pending_shot():
    db = SessionLocal()

    game = Game(
        ships=[
            {"coordinates": ["A1"]},
        ]
    )

    try:
        db.add(game)
        db.commit()
        db.refresh(game)

        session_id = game.session_id

        coordinate = create_shot(
            db=db,
            session_id=session_id,
        )

        assert coordinate == "A1"

    finally:
        db.close()

    db = SessionLocal()

    try:
        saved_game = db.get(Game, session_id)

        assert saved_game is not None
        assert saved_game.outgoing_shots == [
            {
                "coordinate": "A1",
                "result": None,
            }
        ]

    finally:
        saved_game = db.get(Game, session_id)

        if saved_game is not None:
            db.delete(saved_game)
            db.commit()

        db.close()

def test_create_shot_rejects_when_previous_shot_is_pending():
    db = SessionLocal()

    game = Game(
        ships=[
            {"coordinates": ["A1"]},
        ]
    )

    try:
        db.add(game)
        db.commit()
        db.refresh(game)

        session_id = game.session_id

        first_coordinate = create_shot(
            db=db,
            session_id=session_id,
        )

        assert first_coordinate == "A1"

        try:
            create_shot(
                db=db,
                session_id=session_id,
            )

            assert False, "ShotPendingError was not raised"

        except ShotPendingError:
            pass

    finally:
        saved_game = db.get(Game, session_id)

        if saved_game is not None:
            db.delete(saved_game)
            db.commit()

        db.close()

def test_process_shot_result_persists_result():
    db = SessionLocal()

    game = Game(
        ships=[
            {"coordinates": ["A1"]},
        ]
    )

    try:
        db.add(game)
        db.commit()
        db.refresh(game)

        session_id = game.session_id

        coordinate = create_shot(
            db=db,
            session_id=session_id,
        )

        result = process_shot_result(
            db=db,
            session_id=session_id,
            result="hit",
        )

        assert coordinate == "A1"
        assert result is True

    finally:
        db.close()

    db = SessionLocal()

    try:
        saved_game = db.get(Game, session_id)

        assert saved_game is not None
        assert saved_game.outgoing_shots == [
            {
                "coordinate": "A1",
                "result": "hit",
            }
        ]

    finally:
        saved_game = db.get(Game, session_id)

        if saved_game is not None:
            db.delete(saved_game)
            db.commit()

        db.close()

def test_process_shot_result_rejects_without_pending_shot():
    db = SessionLocal()

    game = Game(
        ships=[
            {"coordinates": ["A1"]},
        ]
    )

    try:
        db.add(game)
        db.commit()
        db.refresh(game)

        session_id = game.session_id

        try:
            process_shot_result(
                db=db,
                session_id=session_id,
                result="miss",
            )

            assert False, "NoPendingShotError was not raised"

        except NoPendingShotError:
            pass

    finally:
        saved_game = db.get(Game, session_id)

        if saved_game is not None:
            db.delete(saved_game)
            db.commit()

        db.close()

def test_create_shot_targets_neighbor_after_hit():
    db = SessionLocal()

    game = Game(
        ships=[
            {"coordinates": ["J10"]},
        ]
    )

    try:
        db.add(game)
        db.commit()
        db.refresh(game)

        session_id = game.session_id

        first_coordinate = create_shot(
            db=db,
            session_id=session_id,
        )

        process_shot_result(
            db=db,
            session_id=session_id,
            result="hit",
        )

        second_coordinate = create_shot(
            db=db,
            session_id=session_id,
        )

        assert first_coordinate == "A1"
        assert second_coordinate in {"A2", "B1"}
        assert second_coordinate != first_coordinate

    finally:
        saved_game = db.get(Game, session_id)

        if saved_game is not None:
            db.delete(saved_game)
            db.commit()

        db.close()