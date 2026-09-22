from app.db.session import SessionLocal
from app.domain.fleet.validator import is_valid_fleet
from app.models.game import Game
from app.services.game import create_game, process_opponent_shot

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