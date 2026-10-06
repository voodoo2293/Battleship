from itertools import combinations

from arena.match import play_match
from arena.models import ServiceConfig, TournamentResult

def create_match_pairs(
        services: list[ServiceConfig],
) -> list[tuple[ServiceConfig, ServiceConfig]]:
    return list(combinations(services, 2))

def play_tournament(
        services: list[ServiceConfig],
) -> TournamentResult:
    matches = []

    scores = {
        service.name: 0
        for service in services
    }

    for first_service, second_service in create_match_pairs(services):
        result = play_match(
            first_service,
            second_service,
        )

        matches.append(result)
        scores[result.winner.name] += 1

    max_score = max(scores.values())

    winners = [
        service
        for service in services
        if scores[service.name] == max_score
    ]

    return TournamentResult(
        matches=matches,
        scores=scores,
        winners=winners,
    )