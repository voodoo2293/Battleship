from dataclasses import dataclass

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
class MatchResult:
    winner: ServiceConfig
    loser: ServiceConfig
    turns: int

@dataclass
class TournamentResult:
    matches: list[MatchResult]
    scores: dict[str, int]
    winners: list[ServiceConfig]