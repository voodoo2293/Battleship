from arena.client import ArenaClient
from arena.models import GameSession, ServiceConfig, MatchResult

def create_game_session(
        service: ServiceConfig,
) -> GameSession:
    client = ArenaClient(service.base_url)

    response = client.create_game()

    ships = [
        ship["coordinates"]
        for ship in response["ships"]
    ]

    return GameSession(
        service=service,
        session_id=response["session_id"],
        ships=ships,
    )

def create_match_sessions(
        first_service: ServiceConfig,
        second_service: ServiceConfig,
) -> tuple[GameSession, GameSession]:
    first_session = create_game_session(first_service)
    second_session = create_game_session(second_service)

    return first_session, second_session

def close_game_session(
        session: GameSession,
) -> dict:
    client = ArenaClient(
        session.service.base_url
    )

    return client.close_game(
        session.session_id
    )

def close_match_sessions(
        first_session: GameSession,
        second_session: GameSession,
) -> tuple[dict, dict]:
    first_result = close_game_session(
        first_session
    )
    second_result = close_game_session(
        second_session
    )

    return first_result, second_result

def play_turn(
        shooter: GameSession,
        opponent: GameSession,
) -> tuple[str, str]:
    shooter_client = ArenaClient(
        shooter.service.base_url
    )
    opponent_client = ArenaClient(
        opponent.service.base_url
    )

    shot_response = shooter_client.make_shot(
        shooter.session_id
    )

    coordinate = shot_response["coordinate"]

    opponent_response = opponent_client.send_opponent_shot(
        opponent.session_id,
        coordinate,
    )

    result = opponent_response["result"]

    shooter_client.send_shot_result(
        shooter.session_id,
        result,
    )

    return coordinate, result

def play_match(
        first_service: ServiceConfig,
        second_service: ServiceConfig,
) -> MatchResult:
    first_session, second_session = create_match_sessions(
        first_service,
        second_service,
    )

    hits = {
        first_session.session_id: set(),
        second_session.session_id: set(),
    }

    fleet_cells = {
        first_session.session_id: sum(
            len(ship)
            for ship in first_session.ships
        ),
        second_session.session_id: sum(
            len(ship)
            for ship in second_session.ships
        ),
    }

    shooter = first_session
    opponent = second_session
    turns = 0

    try:
        while True:
            coordinate, result = play_turn(
                shooter,
                opponent,
            )

            turns += 1

            if result in {"hit", "killed"}:
                hits[opponent.session_id].add(
                    coordinate
                )

                if (
                    len(hits[opponent.session_id])
                    == fleet_cells[opponent.session_id]
                ):
                    return MatchResult(
                        winner=shooter.service,
                        loser=opponent.service,
                        turns=turns,
                    )

            if result == "miss":
                shooter, opponent = (
                    opponent,
                    shooter,
                )

    finally:
        close_match_sessions(
            first_session,
            second_session,
        )