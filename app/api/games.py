from uuid import uuid4
from fastapi import APIRouter
from app.schemas.game import GameCreateResponse

router = APIRouter(
    prefix="/games",
    tags=["games"],
)

@router.post(
    "",
    status_code=201,
    response_model=GameCreateResponse,
)
def create_game():
    return {
        "session_id": str(uuid4()),
        "ships": [
            {
                "coordinates": ["A1", "A2", "A3", "A4"]
            },
            {
                "coordinates": ["C1", "C2", "C3"]
            }
        ]
    }