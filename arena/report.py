import json

from pathlib import Path

from arena.models import TournamentResult

def build_tournament_report(
        result: TournamentResult,
) -> dict:
    return {
        "completed": result.completed,
        "scores": result.scores,
        "winners": [
            service.name
            for service in result.winners
        ],
        "failed_matches": [
            {
                "first_service": failure.first_service.name,
                "second_service": failure.second_service.name,
                "reason": failure.reason,
            }
            for failure in result.failed_matches
        ],
        "matches": [
            {
                "winner": match.winner.name,
                "loser": match.loser.name,
                "turns": match.turns,
                "technical": match.technical,
                "reason": match.reason,
                "shots": [
                    {
                        "player": shot.player,
                        "coordinate": shot.coordinate,
                        "expected": shot.expected,
                        "reported": shot.reported,
                    }
                    for shot in match.shots
                ],
            }
            for match in result.matches
        ],
    }

def save_tournament_report(
        result: TournamentResult,
        path: str = "reports/tournament.json",
) -> Path:
    report = build_tournament_report(result)

    report_path = Path(path)

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with report_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=4,
        )

    return report_path