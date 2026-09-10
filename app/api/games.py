from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.game import GameCreateResponse
from app.services.game import create_game as create_game_service

router = APIRouter(
    prefix="/games",
    tags=["games"],
)

@router.post(
    "",
    status_code=201,
    response_model=GameCreateResponse,
)
def create_game(db: Session = Depends(get_db)):
    game = create_game_service(db)

    return {
        "game_id": game.game_id,
        "ships": game.ships,
    }