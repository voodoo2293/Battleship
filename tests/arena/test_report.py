import json

from arena.models import (
    MatchResult,
    ServiceConfig,
    TournamentResult,
    ShotRecord,
)

from arena.report import save_tournament_report

def test_save_tournament_report(tmp_path):
    service_a = ServiceConfig(
        "A",
        "http://service-a",
    )
    service_b = ServiceConfig(
        "B",
        "http://service-b",
    )

    tournament = TournamentResult(
        matches=[
            MatchResult(
                winner=service_b,
                loser=service_a,
                turns=42,
                shots=[
                    ShotRecord(
                        player="B",
                        coordinate="D7",
                        expected="hit",
                        reported="hit",
                    ),
                ],
            )
        ],
        scores={
            "A": 0,
            "B": 1,
        },
        winners=[
            service_b,
        ],
    )

    report_path = tmp_path / "tournament.json"

    save_tournament_report(
        tournament,
        str(report_path),
    )

    with report_path.open(
        encoding="utf-8"
    ) as file:
        report = json.load(file)

        assert report ["scores"] == {
            "A": 0,
            "B": 1,
        }

        assert report ["winners"] == [
            "B",
        ]

        assert report["matches"][0] == {
            "winner": "B",
            "loser": "A",
            "turns": 42,
            "technical": False,
            "reason": None,
            "shots": [
                {
                    "player": "B",
                    "coordinate": "D7",
                    "expected": "hit",
                    "reported": "hit",
                }
            ],
        }
