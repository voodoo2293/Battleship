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
    