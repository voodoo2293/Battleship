from typing import Literal
from uuid import UUID
from pydantic import BaseModel

class ShipResponse(BaseModel):
    coordinates: list[str]

class GameCreateResponse(BaseModel):
    session_id: UUID
    ships: list[ShipResponse]

class OpponentShotRequest(BaseModel):
    coordinate: str

class OpponentShotResponse(BaseModel):
    result: Literal["miss", "hit", "killed"]

class ShotResponse(BaseModel):
    coordinate: str

class ShotResultRequest(BaseModel):
    result: str

class ShotResultResponse(BaseModel):
    status: Literal["accepted"]