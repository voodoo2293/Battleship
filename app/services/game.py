from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.fleet.generator import generate_fleet
from app.domain.shots import get_shot_result
from app.models.game import Game

class GameClosedError(Exception):
    pass

def create_game(db: Session) -> Game:
    fleet = generate_fleet()

    ships = [
        {"coordinates": ship}
        for ship in fleet
    ]

    game = Game(ships=ships)

    db.add(game)
    db.commit()
    db.refresh(game)

    return game

def process_opponent_shot(
    db: Session,
    session_id: UUID,
    coordinate: str,
) -> str | None:
    game = db.get(Game, session_id)

    if game is None:
        return None

    if game.status != "active":
        raise GameClosedError

    result = get_shot_result(
        ships=game.ships,
        received_shots=game.received_shots,
        coordinate=coordinate,
    )

    game.received_shots = [
        *game.received_shots,
        coordinate,
    ]

    db.commit()

    return result