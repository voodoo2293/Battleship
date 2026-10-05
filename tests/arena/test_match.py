from arena.match import (
    create_game_session,
    play_match,
    play_turn,
)
from arena.models import ServiceConfig, GameSession

def test_create_game_session_build_internal_model(monkeypatch):
    service = ServiceConfig(
        "A",
        "http://service-a",
    )

    fake_response = {
        "session_id": "session-a",
        "ships": [
            {
                "coordinates": ["A1", "A2"],
            },
            {
                "coordinates": ["D5"],
            },
        ],
    }

    def fake_create_game(self):
        return fake_response

    monkeypatch.setattr(
        "arena.match.ArenaClient.create_game",
        fake_create_game,
    )

    session = create_game_session(service)

    assert session.service == service
    assert session.session_id == "session-a"
    assert session.ships == [
        ["A1", "A2"],
        ["D5"],
    ]

def test_play_turn_forwards_shot_and_result(monkeypatch):
    shooter_service = ServiceConfig(
        "A",
        "http://service-a",
    )
    opponent_service = ServiceConfig(
        "B",
        "http://service-b",
    )

    shooter = GameSession(
        service=shooter_service,
        session_id="session-a",
        ships=[],
    )

    opponent = GameSession(
        service=opponent_service,
        session_id="session-b",
        ships=[],
    )

    calls = []

    def fake_make_shot(self, session_id):
        calls.append(
            ("shot", self.base_url, session_id)
        )

        return {
            "coordinate": "D7",
        }

    def fake_send_opponent_shot(
            self,
            session_id,
            coordinate,
    ):
        calls.append(
            (
                "opponent-shot",
                self.base_url,
                session_id,
                coordinate,
            )
        )

        return {
            "result": "hit",
        }

    def fake_send_shot_result(
            self,
            session_id,
            result,
    ):
        calls.append(
            (
                "shot-result",
                self.base_url,
                session_id,
                result,
            )
        )

        return {
            "status": "accepted",
        }

    monkeypatch.setattr(
        "arena.match.ArenaClient.make_shot",
        fake_make_shot,
    )
    monkeypatch.setattr(
        "arena.match.ArenaClient.send_opponent_shot",
        fake_send_opponent_shot,
    )
    monkeypatch.setattr(
        "arena.match.ArenaClient.send_shot_result",
        fake_send_shot_result,
    )

    coordinate, result = play_turn(
        shooter,
        opponent,
    )

    assert coordinate == "D7"
    assert result == "hit"

    assert calls == [
        (
            "shot",
            "http://service-a",
            "session-a",
        ),
        (
            "opponent-shot",
            "http://service-b",
            "session-b",
            "D7",
        ),
        (
            "shot-result",
            "http://service-a",
            "session-a",
            "hit",
        ),
    ]

def test_play_match_keeps_turn_after_hit_and_switches_after_miss(
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

    session_a = GameSession(
        service=service_a,
        session_id="session-a",
        ships=[
            ["A1"],
        ],
    )

    session_b = GameSession(
        service=service_b,
        session_id="session-b",
        ships=[
            ["B1", "B2"],
        ],
    )

    def fake_create_match_sessions(
            first_service,
            second_service,
    ):
        return session_a, session_b

    turn_calls = []

    turn_results = iter([
        ("B1", "hit"),
        ("J10", "miss"),
        ("A1", "killed"),
    ])

    def fake_play_turn(shooter, opponent):
        turn_calls.append(
            (
                shooter.service.name,
                opponent.service.name,
            )
        )

        return next(turn_results)

    closed_sessions = []

    def fake_close_match_sessions(
            first_session,
            second_session,
    ):
        closed_sessions.extend([
            first_session.session_id,
            second_session.session_id,
        ])

    monkeypatch.setattr(
        "arena.match.create_match_sessions",
        fake_create_match_sessions,
    )
    monkeypatch.setattr(
        "arena.match.play_turn",
        fake_play_turn,
    )
    monkeypatch.setattr(
        "arena.match.close_match_sessions",
        fake_close_match_sessions,
    )

    result = play_match(
        service_a,
        service_b,
    )

    assert turn_calls == [
        ("A", "B"),
        ("A", "B"),
        ("B", "A"),
    ]

    assert result.winner == service_b
    assert result.loser == service_a
    assert result.turns == 3

    assert closed_sessions == [
        "session-a",
        "session-b",
    ]