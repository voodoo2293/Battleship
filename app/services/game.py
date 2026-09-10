from sqlalchemy.orm import Session

from app.domain.fleet.generator import generate_fleet
from app.models.game import Game

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