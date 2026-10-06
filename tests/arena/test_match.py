import pytest

import httpx

import json

from arena.errors import (
    InvalidFleetError,
    DishonestServiceError,
    InvalidShotError,
    RepeatedShotError,
    ServiceConnectionError,
    ServiceTimeoutError,
    ServiceHTTPError,
    ServiceResponseError,
)

from arena.match import (
    create_game_session,
    create_match_sessions,
    close_match_sessions,
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
            {"coordinates": ["A1", "A2", "A3", "A4"]},
            {"coordinates": ["D1", "E1", "F1"]},
            {"coordinates": ["J1", "J2", "J3"]},
            {"coordinates": ["D4", "E4"]},
            {"coordinates": ["H5", "H6"]},
            {"coordinates": ["B7", "C7"]},
            {"coordinates": ["E7"]},
            {"coordinates": ["J8"]},
            {"coordinates": ["A10"]},
            {"coordinates": ["F10"]},
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
        ["A1", "A2", "A3", "A4"],
        ["D1", "E1", "F1"],
        ["J1", "J2", "J3"],
        ["D4", "E4"],
        ["H5", "H6"],
        ["B7", "C7"],
        ["E7"],
        ["J8"],
        ["A10"],
        ["F10"],
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
        ships=[
            ["D7", "D8"],
        ],
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
        set(),
        set(),
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

    def fake_play_turn(
            shooter,
            opponent,
            opponent_hits,
            shooter_shots,
    ):
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

def test_create_game_session_rejects_invalid_fleet(monkeypatch):
    service = ServiceConfig(
        "A",
        "http://service-a",
    )

    fake_response = {
        "session_id": "session-a",
        "ships": [
            {
                "coordinates": ["A1"],
            },
        ],
    }

    def fake_create_game(self):
        return fake_response

    monkeypatch.setattr(
        "arena.match.ArenaClient.create_game",
        fake_create_game,
    )

    with pytest.raises(InvalidFleetError):
        create_game_session(service)

def test_play_match_awards_technical_win_for_invalid_fleet(
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

    def fake_create_match_sessions(
            first_service,
            second_service,
    ):
        raise InvalidFleetError(service_a)

    monkeypatch.setattr(
        "arena.match.create_match_sessions",
        fake_create_match_sessions,
    )

    result = play_match(
        service_a,
        service_b,
    )

    assert result.winner == service_b
    assert result.loser == service_a
    assert result.turns == 0
    assert result.technical is True
    assert "invalid fleet" in result.reason

def test_create_match_sessions_closes_first_session_if_second_fails(
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
        ships=[],
    )

    calls = []

    def fake_create_game_session(service):
        if service == service_a:
            return session_a

        raise InvalidFleetError(service_b)

    def fake_close_game_session(session):
        calls.append(session.session_id)

        return {
            "status": "closed",
        }

    monkeypatch.setattr(
        "arena.match.create_game_session",
        fake_create_game_session,
    )
    monkeypatch.setattr(
        "arena.match.close_game_session",
        fake_close_game_session,
    )

    with pytest.raises(InvalidFleetError):
        create_match_sessions(
            service_a,
            service_b,
        )

    assert calls == [
        "session-a",
    ]

def test_play_turn_rejects_dishonest_result(
        monkeypatch,
):
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
        ships=[
            ["D7", "D8"],
        ],
    )

    def fake_make_shot(self, session_id):
        return {
            "coordinate": "D7",
        }

    def fake_send_opponent_shot(
            self,
            session_id,
            coordinate,
    ):
        return {
            "result": "miss",
        }

    monkeypatch.setattr(
        "arena.match.ArenaClient.make_shot",
        fake_make_shot,
    )

    monkeypatch.setattr(
        "arena.match.ArenaClient.send_opponent_shot",
        fake_send_opponent_shot,
    )

    with pytest.raises(DishonestServiceError):
        play_turn(
            shooter,
            opponent,
            set(),
            set(),
        )

def test_play_match_awards_technical_loss_for_dishonest_service(
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
            ["D7"],
        ],
    )

    def fake_create_match_sessions(
            first_service,
            second_service,
    ):
        return session_a, session_b

    def fake_play_turn(
            shooter,
            opponent,
            opponent_hits,
            shooter_shots,
    ):
        raise DishonestServiceError(
            service=service_b,
            coordinate="D7",
            expected="killed",
            actual="miss",
        )

    closed = []

    def fake_close_match_sessions(
            first_session,
            second_session,
    ):
        closed.extend([
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

    assert result.winner == service_a
    assert result.loser == service_b
    assert result.turns == 0
    assert result.technical is True
    assert "expected killed" in result.reason

    assert len(result.shots) == 1

    shot = result.shots[0]

    assert shot.player == "A"
    assert shot.coordinate == "D7"
    assert shot.expected == "killed"
    assert shot.reported == "miss"

    assert closed == [
        "session-a",
        "session-b",
    ]

def test_play_turn_rejects_invalid_shot_coordinate(
        monkeypatch,
):
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

    def fake_make_shot(self, sesion_id):
        return {
            "coordinate": "K1",
        }

    monkeypatch.setattr(
        "arena.match.ArenaClient.make_shot",
        fake_make_shot,
    )

    with pytest.raises(InvalidShotError):
        play_turn(
            shooter,
            opponent,
            set(),
            set(),
        )

def test_play_match_awards_technical_loss_for_invalid_shot(
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
        ships=[],
    )

    session_b = GameSession(
        service=service_b,
        session_id="session-b",
        ships=[],
    )

    def fake_create_match_sessions(
            first_service,
            second_service,
    ):
        return session_a, session_b

    def fake_play_turn(
            shooter,
            opponent,
            opponent_hits,
            shooter_shots,
    ):
        raise InvalidShotError(
            service=service_a,
            coordinate="K1",
        )

    def fake_close_match_sessions(
            first_session,
            second_session,
    ):
        pass

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

    assert result.winner == service_b
    assert result.loser == service_a
    assert result.turns == 0
    assert result.technical is True
    assert "K1" in result.reason

def test_play_turn_rejects_repeated_shot(
        monkeypatch,
):
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

    def fake_make_shot(self, session_id):
        return {
            "coordinate": "D7",
        }

    monkeypatch.setattr(
        "arena.match.ArenaClient.make_shot",
        fake_make_shot,
    )

    with pytest.raises(RepeatedShotError):
        play_turn(
            shooter,
            opponent,
            set(),
            {"D7"},
        )

def test_play_match_awards_technical_loss_for_repeated_shot(
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
        ships=[],
    )

    session_b = GameSession(
        service=service_b,
        session_id="session-b",
        ships=[],
    )

    def fake_create_match_sessions(
            first_service,
            second_service,
    ):
        return session_a, session_b

    def fake_play_turn(
            shooter,
            opponent,
            opponent_hits,
            shooter_shots,
    ):
        raise RepeatedShotError(
            service=service_a,
            coordinate="D7",
        )

    def fake_close_match_sessions(
            first_session,
            second_session,
    ):
        pass

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

    assert result.winner == service_b
    assert result.loser == service_a
    assert result.turns == 0
    assert result.technical is True
    assert "D7" in result.reason

def test_play_turn_converts_timeout_to_service_error(
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

    shooter = GameSession(
        service=service_a,
        session_id="session-a",
        ships=[],
    )

    opponent = GameSession(
        service=service_b,
        session_id="session-b",
        ships=[],
    )

    def fake_make_shot(self, session_id):
        raise httpx.ReadTimeout(
            "timeout"
        )

    monkeypatch.setattr(
        "arena.match.ArenaClient.make_shot",
        fake_make_shot,
    )

    with pytest.raises(ServiceTimeoutError) as error:
        play_turn(
            shooter,
            opponent,
            set(),
            set(),
        )

    assert error.value.service == service_a

def test_play_match_awards_technical_loss_for_timeout(
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
        ships=[],
    )

    session_b = GameSession(
        service=service_b,
        session_id="session-b",
        ships=[],
    )

    def fake_create_match_sessions(
            first_service,
            second_service,
    ):
        return session_a, session_b

    def fake_play_turn(
            shooter,
            opponent,
            opponent_hits,
            shooter_shots,
    ):
        raise ServiceTimeoutError(
            service_a
        )

    def fake_close_match_sessions(
            first_session,
            second_session,
    ):
        pass

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

    assert result.winner == service_b
    assert result.loser == service_a
    assert result.turns == 0
    assert result.technical is True
    assert "timeout" in result.reason

def test_play_turn_converts_connection_error_to_service_error(
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

    shooter = GameSession(
        service=service_a,
        session_id="session-a",
        ships=[],
    )

    opponent = GameSession(
        service=service_b,
        session_id="session-b",
        ships=[],
    )

    def fake_make_shot(self, session_id):
        raise httpx.ConnectError(
            "connection failde"
        )

    monkeypatch.setattr(
        "arena.match.ArenaClient.make_shot",
        fake_make_shot,
    )

    with pytest.raises(ServiceConnectionError) as error:
        play_turn(
            shooter,
            opponent,
            set(),
            set(),
        )

    assert error.value.service == service_a

def test_play_match_awards_technical_loss_for_connection_error(
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
        ships=[],
    )

    session_b = GameSession(
        service=service_b,
        session_id="session-b",
        ships=[],
    )

    def fake_create_match_sessions(
            first_service,
            second_service,
    ):
        return session_a, session_b

    def fake_play_turn(
            shooter,
            opponent,
            opponent_hits,
            shooter_shots,
    ):
        raise ServiceConnectionError(
            service_a
        )

    def fake_close_match_sessions(
            first_session,
            second_session,
    ):
        pass

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

    assert result.winner == service_b
    assert result.loser == service_a
    assert result.turns == 0
    assert result.technical is True
    assert "unavailable" in result.reason

def test_play_turn_converts_http_error_to_service_rror(
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

    shooter = GameSession(
        service=service_a,
        session_id="session-a",
        ships=[],
    )

    opponent = GameSession(
        service=service_b,
        session_id="session-b",
        ships=[],
    )

    opponent = GameSession(
        service=service_b,
        session_id="session-b",
        ships=[],
    )

    def fake_make_shot(self, session_id):
        request = httpx.Request(
            "POST",
            "http://service-a/shot",
        )
        response = httpx.Response(
            500,
            request=request,
        )

        raise httpx.HTTPStatusError(
            "server error",
            request=request,
            response=response,
        )

    monkeypatch.setattr(
        "arena.match.ArenaClient.make_shot",
        fake_make_shot,
    )

    with pytest.raises(ServiceHTTPError) as error:
        play_turn(
            shooter,
            opponent,
            set(),
            set(),
        )

    assert error.value.service == service_a
    assert error.value.status_code == 500

def test_play_turn_rejects_invalid_shot_response(
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

    shooter = GameSession(
        service=service_a,
        session_id="session-a",
        ships=[],
    )

    opponent = GameSession(
        service=service_b,
        session_id="session-b",
        ships=[],
    )

    def fake_make_shot(self, session_id):
        return {}

    monkeypatch.setattr(
        "arena.match.ArenaClient.make_shot",
        fake_make_shot,
    )

    with pytest.raises(ServiceResponseError) as error:
        play_turn(
            shooter,
            opponent,
            set(),
            set(),
        )

        assert error.value.service == service_a

def test_play_turn_rejects_invalid_opponent_response(
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

    shooter = GameSession(
        service=service_a,
        session_id="session-a",
        ships=[],
    )

    opponent = GameSession(
        service=service_b,
        session_id="session-b",
        ships=[],
    )

    def fake_make_shot(self, session_id):
        return {
            "coordinate": "D7",
        }

    def fake_send_opponent_shot(
            self,
            session_id,
            coordinate,
    ):
        return {
            "result": "unknown",
        }

    monkeypatch.setattr(
        "arena.match.ArenaClient.make_shot",
        fake_make_shot,
    )

    monkeypatch.setattr(
        "arena.match.ArenaClient.send_opponent_shot",
        fake_send_opponent_shot,
    )

    with pytest.raises(ServiceResponseError) as error:
        play_turn(
            shooter,
            opponent,
            set(),
            set(),
        )

    assert error.value.service == service_b

def test_play_turn_rejects_invalid_shot_result_response(
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

    shooter = GameSession(
        service=service_a,
        session_id="session-a",
        ships=[],
    )

    opponent = GameSession(
        service=service_b,
        session_id="session-b",
        ships=[],
    )

    def fake_make_shot(self, session_id):
        return {
            "coordinate": "D7",
        }

    def fake_send_opponent_shot(
            self,
            session_id,
            coordinate,
    ):
        return {
            "result": "miss",
        }

    def fake_send_shot_result(
            self,
            session_id,
            result,
    ):
        return {
            "status": "wrong",
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

    with pytest.raises(ServiceResponseError) as error:
        play_turn(
            shooter,
            opponent,
            set(),
            set(),
        )

    assert error.value.service == service_a

def test_play_turn_rejects_invalid_json(
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

    shooter = GameSession(
        service=service_a,
        session_id="session-a",
        ships=[],
    )

    opponent = GameSession(
        service=service_b,
        session_id="session-b",
        ships=[],
    )

    def fake_make_shot(self, session_id):
        raise json.JSONDecodeError(
            "invalid JSON",
            "",
            0,
        )

    monkeypatch.setattr(
        "arena.match.ArenaClient.make_shot",
        fake_make_shot,
    )

    with pytest.raises(ServiceResponseError) as error:
        play_turn(
            shooter,
            opponent,
            set(),
            set(),
        )

    assert error.value.service == service_a
    assert "invalid JSON" in str(error.value)

def test_create_game_session_converts_timout_to_service_error(
        monkeypatch,
):
    service = ServiceConfig(
        "A",
        "http://service-a",
    )

    def fake_create_game(self):
        raise httpx.ReadTimeout(
            "timeout"
        )

    monkeypatch.setattr(
        "arena.match.ArenaClient.create_game",
        fake_create_game,
    )

    with pytest.raises(ServiceTimeoutError) as error:
        create_game_session(service)

    assert error.value.service == service

def test_create_game_session_rejects_invalid_response(
        monkeypatch,
):
    service = ServiceConfig(
        "A",
        "http://service-a",
    )

    def fake_create_game(self):
        return {
            "session_id": "session-a",
            "ships": "wrong",
        }

    monkeypatch.setattr(
        "arena.match.ArenaClient.create_game",
        fake_create_game,
    )

    with pytest.raises(ServiceResponseError) as error:
        create_game_session(service)

    assert error.value.service == service

def test_play_match_awards_technical_loss_if_game_creation_fails(
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

    def fake_create_match_sessions(
            first_service,
            second_service,
    ):
        raise ServiceTimeoutError(
            service_b
        )

    monkeypatch.setattr(
        "arena.match.create_match_sessions",
        fake_create_match_sessions,
    )

    result = play_match(
        service_a,
        service_b,
    )

    assert result.winner == service_a
    assert result.loser == service_b
    assert result.turns == 0
    assert result.technical is True
    assert "timeout" in result.reason

def test_close_match_sessions_attempts_both_closes(
        monkeypatch,
):
    service_a = ServiceConfig("A", "http://service-a",)
    service_b = ServiceConfig("B", "http://service-b",)

    session_a = GameSession(
        service=service_a,
        session_id="session-a",
        ships=[],
    )

    session_b = GameSession(
        service=service_b,
        session_id="session-b",
        ships=[],
    )

    calls = []

    def fake_close_game_session(session):
        calls.append(session.session_id)

        if session == session_a:
            raise RuntimeError("close failed")

        return {"status": "closed"}

    monkeypatch.setattr(
        "arena.match.close_game_session",
        fake_close_game_session,
    )

    results = close_match_sessions(
        session_a,
        session_b,
    )

    assert calls == ["session-a", "session-b",]
    assert results == (None, {"status": "closed"})

def test_play_match_saves_shot_history(
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
            ["D7"],
        ],
    )

    def fake_create_match_sessions(
            first_service,
            second_service,
    ):
        return session_a, session_b

    def fake_play_turn(
            shooter,
            opponent,
            opponent_hits,
            shooter_shots,
    ):
        return "D7", "killed"

    def fake_close_match_sessions(
            first_session,
            second_session,
    ):
        pass

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

    assert len(result.shots) == 1

    shot = result.shots[0]

    assert shot.player == "A"
    assert shot.coordinate == "D7"
    assert shot.expected == "killed"
    assert shot.reported == "killed"

@pytest.mark.parametrize("failure", ["http", "connection"])

def test_opponent_request_failure_blames_opponent(
    monkeypatch,
    failure,
):
    service_a = ServiceConfig(
        "A", 
        "http://service-a",
    )
    
    service_b = ServiceConfig(
        "B", 
        "http://service-b",
    )

    shooter = GameSession(
        service_a, 
        "session-a", 
        [],
    )
    
    opponent = GameSession(
        service_b, 
        "session-b", 
        [],
    )

    def fake_make_shot(
            self, 
            session_id,
    ):
        return {
            "coordinate": "D7",
        }

    def fake_opponent_shot(
            self, 
            session_id, 
            coordinate,
    ):
        request = httpx.Request(
            "POST",
            "http://service-b/game/session-b/opponent-shot",
        )

        if failure == "http":
            response = httpx.Response(500, request=request)
            raise httpx.HTTPStatusError(
                "Server error",
                request=request,
                response=response,
            )

        raise httpx.ConnectError(
            "Connection failed",
            request=request,
        )

    monkeypatch.setattr(
        "arena.match.ArenaClient.make_shot",
        fake_make_shot,
    )
    monkeypatch.setattr(
        "arena.match.ArenaClient.send_opponent_shot",
        fake_opponent_shot,
    )

    expected_error = (
        ServiceHTTPError
        if failure == "http"
        else ServiceConnectionError
    )

    with pytest.raises(expected_error) as error:
        play_turn(
            shooter,
            opponent,
            set(),
            set(),
        )

    assert error.value.service == service_b

@pytest.mark.parametrize(
    "failure",
    ["list_result", "dict_result", "ack_json"],
)
def test_invalid_response_blames_responsible_service(
    monkeypatch,
    failure,
):
    service_a = ServiceConfig(
        "A", 
        "http://service-a",
    )
    
    service_b = ServiceConfig(
        "B", 
        "http://service-b",
    )

    shooter = GameSession(
        service_a, 
        "session-a", 
        [],
    )
    
    opponent = GameSession(
        service_b, 
        "session-b", 
        [],
    )

    def fake_make_shot(
            self, 
            session_id,
    ):
        return {
            "coordinate": "D7",
        }

    def fake_opponent_shot(
            self,
            session_id,
            coordinate,
    ):
        if failure == "list_result":
            return {
                "result": [],
            }
        if failure == "dict_result":
            return {
                "result": {},
            }
        return {
            "result": "miss",
        }
    def fake_send_result(
            self,
            session_id,
            result,
    ):
        raise json.JSONDecodeError(
            "Invalid JSON",
            "",
            0,
        )
    monkeypatch.setattr(
        "arena.match.ArenaClient.make_shot",
        fake_make_shot,
    )
    monkeypatch.setattr(
        "arena.match.ArenaClient.send_opponent_shot",
        fake_opponent_shot,
    )
    monkeypatch.setattr(
        "arena.match.ArenaClient.send_shot_result",
        fake_send_result,
    )

    with pytest.raises(ServiceResponseError) as error:
        play_turn(
            shooter,
            opponent,
            set(),
            set(),
        )

    expected_service = (
        service_a if failure == "ack_json" else service_b
    )
    assert error.value.service == expected_service

def test_creation_error_survives_cleanup_failure(
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
        ships=[],
    )

    close_calls = []

    def fake_create_game_session(service):
        if service == service_a:
            return session_a

        raise ServiceTimeoutError(
            service_b,
        )

    def fake_close_game_session(session):
        close_calls.append(
            session.session_id,
        )

        raise httpx.ConnectError(
            "Cleanup connection failed",
        )

    monkeypatch.setattr(
        "arena.match.create_game_session",
        fake_create_game_session,
    )
    monkeypatch.setattr(
        "arena.match.close_game_session",
        fake_close_game_session,
    )

    result = play_match(
        service_a,
        service_b,
    )

    assert result.technical is True
    assert result.winner == service_a
    assert result.loser == service_b
    assert result.turns == 0
    assert "timeout" in result.reason
    assert close_calls == ["session-a"]