from dataclasses import dataclass, field

@dataclass(frozen=True)
class ServiceConfig:
    name: str
    base_url: str

@dataclass
class GameSession:
    service: ServiceConfig
    session_id: str
    ships: list[list[str]]

@dataclass
class ShotRecord:
    player: str
    coordinate: str
    expected: str
    reported: str
@dataclass
class MatchResult:
    winner: ServiceConfig
    loser: ServiceConfig
    turns: int
    technical:bool = False
    reason: str | None = None
    shots: list[ShotRecord] = field(
        default_factory=list
    )

@dataclass
class TournamentResult:
    matches: list[MatchResult]
    scores: dict[str, int]
    winners: list[ServiceConfig]
