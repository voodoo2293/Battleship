import logging
from itertools import combinations

from arena.match import play_match
from arena.models import (
    FailedMatch,
    ServiceConfig,
    TournamentResult,
)
from arena.report import save_tournament_report

logger = logging.getLogger(__name__)

def create_match_pairs(
        services: list[ServiceConfig],
) -> list[tuple[ServiceConfig, ServiceConfig]]:
    return list(combinations(services, 2))

def play_tournament(
        services: list[ServiceConfig],
        report_path: str | None = None,
) -> TournamentResult:
    result = TournamentResult(
        matches=[],
        scores={
            service.name: 0
            for service in services
        },
        winners=[],
        completed=False,
    )

    if report_path is not None:
        save_tournament_report(
            result,
            report_path,
        )

    for first_service, second_service in create_match_pairs(services):
        try:
            match = play_match(
                first_service,
                second_service,
            )
        except Exception as error:
            logger.exception(
                "Unexpected arena error in match %s vs %s",
                first_service.name,
                second_service.name,
            )

            result.failed_matches.append(
                FailedMatch(
                    first_service=first_service,
                    second_service=second_service,
                    reason=f"{type(error).__name__}: {error}",
                )
            )
        else:
            result.matches.append(match)
            result.scores[match.winner.name] += 1

        if report_path is not None:
            save_tournament_report(
                result,
                report_path,
            )

    result.completed = not result.failed_matches

    if result.scores and result.completed:
        max_score = max(result.scores.values())

        result.winners = [
            service
            for service in services
            if result.scores[service.name] == max_score
        ]

    if report_path is not None:
        save_tournament_report(
            result,
            report_path,
        )

    return result