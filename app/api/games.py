from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.domain.fleet.coordinates import parse_coordinate
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.game import (
    GameCreateResponse,
    OpponentShotRequest,
    OpponentShotResponse,
)
from app.services.game import (
    GameClosedError,
    create_game as create_game_service,
    process_opponent_shot,
)

router = APIRouter(
    prefix="/game",
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
        "session_id": game.session_id,
        "ships": game.ships,
    }

@router.post(
    "/{session_id}/opponent-shot",
    response_model=OpponentShotResponse,
)
def opponent_shot(
    session_id: UUID,
    request: OpponentShotRequest,
    db: Session = Depends(get_db),
):
    try:
        parse_coordinate(request.coordinate)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid coordinate",
        )

    try:
        result = process_opponent_shot(
            db=db,
            session_id=session_id,
            coordinate=request.coordinate,
        )
    except GameClosedError:
        raise HTTPException(
            status_code=410,
            detail="Game session is closed",
        )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Game session not found",
        )

    return {
        "result": result,
    }