from uuid import UUID
from pydantic import BaseModel

class ShipResponse(BaseModel):
    coordinates: list[str]

class GameCreateResponse(BaseModel):
    game_id: UUID
    ships: list[ShipResponse]