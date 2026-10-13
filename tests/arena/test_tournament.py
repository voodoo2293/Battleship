import json

import pytest

from arena.models import ServiceConfig, MatchResult
from arena.tournament import create_match_pairs, play_tournament

def test_create_match_pairs_returns_each_pair_once():
    services = [
        ServiceConfig("A", "http://a"),
        ServiceConfig("B", "http://b"),
        ServiceConfig("C", "http://c"),
    ]

    pairs = create_match_pairs(services)

    pair_names = [
        (first.name, second.name)
        for first, second in pairs
    ]

    assert pair_names == [
        ("A", "B"),
        ("A", "C"),
        ("B", "C"),
    ]

def test_play_tournament_counts_scores_and_winner(monkeypatch):
    services = [
        ServiceConfig("A", "http://a"),
        ServiceConfig("B", "http://b"),
        ServiceConfig("C", "http://c"),
    ]

    results = iter([
        MatchResult(
            winner=services[1],
            loser=services[0],
            turns=100,
        ),
        MatchResult(
            winner=services[2],
            loser=services[0],
            turns=110,
        ),
        MatchResult(
            winner=services[2],
            loser=services[1],
            turns=120,
        ),
    ])

    def fake_play_match(first_service, second_service):
        return next(results)

    monkeypatch.setattr(
        "arena.tournament.play_match",
        fake_play_match,
    )

    result = play_tournament(services)

    assert result.scores == {
        "A": 0,
        "B": 1,
        "C": 2,
    }

    assert [winner.name for winner in result.winners] == [
        "C"
    ]

    assert len(result.matches) == 3

def test_play_tournament_returns_all_winners_on_tie(monkeypatch):
    services = [
        ServiceConfig("A", "http://a"),
        ServiceConfig("B", "http://b"),
        ServiceConfig("C", "http://c"),
    ]

    results = iter([
        MatchResult(
            winner=services[0],
            loser=services[1],
            turns=100,
        ),
        MatchResult(
            winner=services[2],
            loser=services[0],
            turns=110,
        ),
        MatchResult(
            winner=services[1],
            loser=services[2],
            turns=120,
        ),
    ])

    def fake_play_match(first_service, second_service):
        return next(results)

    monkeypatch.setattr(
        "arena.tournament.play_match",
        fake_play_match,
    )

    result = play_tournament(services)

    assert result.scores == {
        "A": 1,
        "B": 1,
        "C": 1,
    }

    assert [winner.name for winner in result.winners] == [
        "A",
        "B",
        "C",
    ]

def test_tournament_continues_after_technical_defeat(
        monkeypatch,
):
    service_a = ServiceConfig(
        "A",
        "http://service-a",
    )
    service_b = ServiceConfig(
        "B",
        "http://service-b",
    )
    service_c = ServiceConfig(
        "C",
        "http://service-c",
    )

    results = [
        MatchResult(
            winner=service_b,
            loser=service_a,
            turns=0,
            technical=True,
            reason="A unavailable",
        ),
        MatchResult(
            winner=service_c,
            loser=service_a,
            turns=20,
        ),
        MatchResult(
            winner=service_c,
            loser=service_b,
            turns=30,
        ),
    ]

    calls = []

    def fake_play_match(
            first_service,
            second_service,
    ):
        calls.append(
            (
                first_service.name,
                second_service.name,
            )
        )

        return results[len(calls) - 1]

    monkeypatch.setattr(
        "arena.tournament.play_match",
        fake_play_match,
    )

    result = play_tournament(
        [
            service_a,
            service_b,
            service_c,
        ]
    )

    assert calls == [
        ("A", "B"),
        ("A", "C"),
        ("B", "C"),
    ]

    assert result.scores == {
        "A": 0,
        "B": 1,
        "C": 2,
    }

    assert result.winners == [
        service_c,
    ]

def test_tournament_continues_after_unexpected_error(
        monkeypatch,
):
    service_a = ServiceConfig(
        "A",
        "http://service-a",
    )
    service_b = ServiceConfig(
        "B",
        "http://service-b",
    )
    service_c = ServiceConfig(
        "C",
        "http://service-c",
    )

    calls = []

    def fake_play_match(
            first_service,
            second_service,
    ):
        calls.append(
            (
                first_service.name,
                second_service.name,
            )
        )

        if len(calls) == 2:
            raise RuntimeError(
                "unexpected failure"
            )

        return MatchResult(
            winner=second_service,
            loser=first_service,
            turns=10,
        )

    monkeypatch.setattr(
        "arena.tournament.play_match",
        fake_play_match,
    )

    result = play_tournament(
        [
            service_a,
            service_b,
            service_c,
        ]
    )

    assert calls == [
        ("A", "B"),
        ("A", "C"),
        ("B", "C"),
    ]

    assert len(result.matches) == 2

    assert result.scores == {
        "A": 0,
        "B": 1,
        "C": 1,
    }

    assert result.winners == []

    assert len(result.failed_matches) == 1

    failure = result.failed_matches[0]

    assert failure.first_service == service_a
    assert failure.second_service == service_c

    assert failure.reason == (
        "RuntimeError: unexpected failure"
    )

def test_tournament_handles_all_matches_failing(
        monkeypatch,
):
    service_a = ServiceConfig(
        "A",
        "http://service-a",
    )
    service_b = ServiceConfig(
        "B",
        "http://service-b",
    )
    service_c = ServiceConfig(
        "C",
        "http://service-c",
    )

    def fake_play_match(
            first_service,
            second_service,
    ):
        raise RuntimeError(
            "unexpected failure"
        )

    monkeypatch.setattr(
        "arena.tournament.play_match",
        fake_play_match,
    )

    result = play_tournament(
        [
            service_a,
            service_b,
            service_c,
        ]
    )

    assert result.matches == []

    assert result.scores == {
        "A": 0,
        "B": 0,
        "C": 0,
    }

    assert result.winners == []

    assert len(result.failed_matches) == 3

@pytest.mark.parametrize(
    "fail_second_match",
    [
        False,
        True,
    ],
)
def test_tournament_saves_progress_between_matches(
    monkeypatch,
    tmp_path,
    fail_second_match,
):
    service_a = ServiceConfig(
        "A",
        "http://service-a",
    )
    service_b = ServiceConfig(
        "B",
        "http://service-b",
    )
    service_c = ServiceConfig(
        "C",
        "http://service-c",
    )

    report_path = tmp_path / "tournament.json"
    calls = []

    def fake_play_match(
            first_service,
            second_service,
    ):
        with report_path.open(
            encoding="utf-8",
        ) as file:
            report = json.load(file)

        assert report["completed"] is False
        assert report["winners"] == []

        previous_matches = len(calls)

        if fail_second_match and previous_matches == 2:
            assert len(report["matches"]) == 1
            assert len(report["failed_matches"]) == 1

            assert report["failed_matches"][0] == {
                "first_service": "A",
                "second_service": "C",
                "reason": "RuntimeError: unexpected failure",
            }
        else:
            assert len(report["matches"]) == previous_matches
            assert report["failed_matches"] == []

        calls.append(
            (
                first_service.name,
                second_service.name,
            )
        )

        if fail_second_match and len(calls) == 2:
            raise RuntimeError(
                "unexpected failure"
            )

        return MatchResult(
            winner=second_service,
            loser=first_service,
            turns=10,
        )

    monkeypatch.setattr(
        "arena.tournament.play_match",
        fake_play_match,
    )

    result = play_tournament(
        [
            service_a,
            service_b,
            service_c,
        ],
        report_path=str(report_path),
    )

    with report_path.open(
        encoding="utf-8",
    ) as file:
        report = json.load(file)

    assert calls == [
        ("A", "B"),
        ("A", "C"),
        ("B", "C"),
    ]

    assert report["scores"] == result.scores

    if fail_second_match:
        assert report["completed"] is False
        assert report["winners"] == []
        assert len(report["matches"]) == 2
        assert len(report["failed_matches"]) == 1

        assert report["scores"] == {
            "A": 0,
            "B": 1,
            "C": 1,
        }
    else:
        assert report["completed"] is True
        assert report["winners"] == [
            "C",
        ]
        assert len(report["matches"]) == 3
        assert report["failed_matches"] == []

        assert report["scores"] == {
            "A": 0,
            "B": 1,
            "C": 2,
        }