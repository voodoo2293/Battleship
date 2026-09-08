from app.db.session import SessionLocal
from app.domain.fleet.validator import is_valid_fleet
from app.models.game import Game
from app.services.game import create_game

def test_create_game_persists_game_in_database():
    db = SessionLocal()

    try:
        game = create_game(db)
        game_id = game.game_id
    finally:
        db.close()

    db = SessionLocal()

    try:
        saved_game = db.get(Game, game_id)

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
        saved_game = db.get(Game, game_id)

        if saved_game is not None:
            db.delete(saved_game)
            db.commit()

        db.close()