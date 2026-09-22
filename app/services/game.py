from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.fleet.generator import generate_fleet
from app.domain.shots import choose_shot_coordinate, get_shot_result
from app.models.game import Game

class GameClosedError(Exception):
    pass

class ShotPendingError(Exception):
    pass

class NoPendingShotError(Exception):
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

def create_shot(
    db: Session,
    session_id: UUID,
) -> str | None:
    game = db.get(Game, session_id)

    if game is None:
        return None

    if game.status != "active":
        raise GameClosedError

    if (
        game.outgoing_shots
        and game.outgoing_shots[-1]["result"] is None
    ):
        raise ShotPendingError

    coordinate = choose_shot_coordinate(game.outgoing_shots)

    if coordinate is None:
        raise ShotPendingError

    game.outgoing_shots = [
        *game.outgoing_shots,
        {
            "coordinate": coordinate,
            "result": None,
        }
    ]

    db.commit()

    return coordinate

def process_shot_result(
    db: Session,
    session_id: UUID,
    result: str,
) -> bool | None:
    game = db.get(Game, session_id)

    if game is None:
        return None

    if game.status != "active":
        raise GameClosedError

    if (
        not game.outgoing_shots
        or game.outgoing_shots[-1]["result"] is not None
    ):
        raise NoPendingShotError

    updated_shots = [
        *game.outgoing_shots[:-1],
        {
            "coordinate": game.outgoing_shots[-1]["coordinate"],
            "result": result,
        },
    ]

    game.outgoing_shots = updated_shots

    db.commit()

    return True