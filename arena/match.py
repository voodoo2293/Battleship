import httpx

import logging

from arena.client import ArenaClient
from arena.models import (
    GameSession,
    MatchResult,
    ServiceConfig,
    ShotRecord,
)

from arena.errors import (
    DishonestServiceError,
    InvalidFleetError,
    InvalidShotError,
    RepeatedShotError,
    ServiceTimeoutError,
    ServiceHTTPError,
    ServiceConnectionError,
    ServiceResponseError,
)
from arena.validation import (
    get_expected_shot_result,
    is_valid_fleet,
    parse_coordinate,
)

logger = logging.getLogger(__name__)

def create_game_session(
        service: ServiceConfig,
) -> GameSession:
    client = ArenaClient(service.base_url)

    try:
        response = client.create_game()
    except httpx.HTTPStatusError as error:
        raise ServiceHTTPError(
            service,
            error.response.status_code,
        )
    except httpx.TimeoutException:
        raise ServiceTimeoutError(service)
    except httpx.RequestError:
        raise ServiceConnectionError(service)
    except ValueError:
        raise ServiceResponseError(
            service,
            "invalid JSON",
        )

    if (
        not isinstance(response, dict)
        or not isinstance(response.get("session_id"), str)
        or not isinstance(response.get("ships"), list)
    ):
        raise ServiceResponseError(
            service,
            "invalid game creation response",
        )

    for ship in response["ships"]:
        if (
            not isinstance(ship, dict)
            or not isinstance(
                ship.get("coordinates"),
                list,
            )
            or not all(
                isinstance(coordinate, str)
                for coordinate in ship["coordinates"]
            )
        ):
            raise ServiceResponseError(
                service,
                "invalid ships structure",
            )
        
    ships = [
        ship["coordinates"]
        for ship in response["ships"]
    ]

    if not is_valid_fleet(ships):
        raise InvalidFleetError(service)

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

    try:
        second_session = create_game_session(second_service)
    except Exception:
        try:
            close_game_session(first_session)
        except Exception:
            logger.exception(
                "Failed to close session %s on service %s",
                first_session.session_id,
                first_session.service.name,
            )
        raise

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
) -> tuple[dict | None, dict | None]:
    first_result = None
    second_result = None

    try:
        first_result = close_game_session(first_session)
    except Exception:
        logger.exception(
            "Failed to close session %s on service %s",
            first_session.session_id,
            first_session.service.name,
        )
        
    try:
        second_result = close_game_session(second_session)
    except Exception:
        logger.exception(
            "Failed to close session %s on service %s",
            second_session.session_id,
            second_session.service.name,
        )

    return first_result, second_result

def play_turn(
        shooter: GameSession,
        opponent: GameSession,
        opponent_hits: set[str],
        shooter_shots: set[str],
) -> tuple[str, str]:
    shooter_client = ArenaClient(
        shooter.service.base_url
    )
    opponent_client = ArenaClient(
        opponent.service.base_url
    )

    try:
        shot_response = shooter_client.make_shot(
            shooter.session_id
        )
    except httpx.HTTPStatusError as error:
        raise ServiceHTTPError(
            shooter.service,
            error.response.status_code,
        )
    except httpx.TimeoutException:
        raise ServiceTimeoutError(
            shooter.service
        )
    except httpx.RequestError:
        raise ServiceConnectionError(
            shooter.service
        )
    except ValueError:
        raise ServiceResponseError(
            shooter.service,
            "invalid JSON",
        )

    if (
        not isinstance(shot_response, dict)
        or "coordinate" not in shot_response
        or not isinstance(
            shot_response["coordinate"],
            str,
        )
    ):
        raise ServiceResponseError(
            shooter.service,
            "missing or invalid coordinate",
        )
    
    coordinate = shot_response["coordinate"]

    try:
        parse_coordinate(coordinate)
    except ValueError:
        raise InvalidShotError(
            service=shooter.service,
            coordinate=coordinate,
        )

    if coordinate in shooter_shots:
        raise RepeatedShotError(
            service=shooter.service,
            coordinate=coordinate,
        )

    shooter_shots.add(coordinate)

    try:
        opponent_response = opponent_client.send_opponent_shot(
            opponent.session_id,
            coordinate,
        )
    except httpx.HTTPStatusError as error:
        raise ServiceHTTPError(
            opponent.service,
            error.response.status_code,
        )
    except httpx.TimeoutException:
        raise ServiceTimeoutError(
            opponent.service
        )
    except httpx.RequestError:
        raise ServiceConnectionError(
            opponent.service
        )
    except ValueError:
        raise ServiceResponseError(
            opponent.service,
            "invalid JSON",
        )

    if (
        not isinstance(opponent_response, dict)
        or not isinstance(
            opponent_response.get("result"),
            str,
        )
        or opponent_response["result"]
        not in {"miss", "hit", "killed"}
    ):
        raise ServiceResponseError(
            opponent.service,
            "missing or invalid result",
        )
    
    result = opponent_response["result"]

    expected_result = get_expected_shot_result(
        opponent.ships,
        opponent_hits,
        coordinate,
    )

    if result != expected_result:
        raise DishonestServiceError(
            service=opponent.service,
            coordinate=coordinate,
            expected=expected_result,
            actual=result,
        )

    try:
        shot_result_response = shooter_client.send_shot_result(
            shooter.session_id,
            result,
        )
    except httpx.HTTPStatusError as error:
        raise ServiceHTTPError(
            shooter.service,
            error.response.status_code,
        )
    except httpx.TimeoutException:
        raise ServiceTimeoutError(
            shooter.service
        )
    except httpx.RequestError:
        raise ServiceConnectionError(
            shooter.service
        )
    except ValueError:
        raise ServiceResponseError(
            shooter.service,
            "invalid JSON",
        )

    if (
        not isinstance(shot_result_response, dict)
        or shot_result_response.get("status") != "accepted"
    ):
        raise ServiceResponseError(
            shooter.service,
            "invalid shot result acknowledgement",
        )

    return coordinate, result

def play_match(
        first_service: ServiceConfig,
        second_service: ServiceConfig,
) -> MatchResult:
    try:
        first_session, second_session = create_match_sessions(
            first_service,
            second_service,
        )
    except (
        InvalidFleetError,
        ServiceConnectionError,
        ServiceHTTPError,
        ServiceResponseError,
        ServiceTimeoutError,
    ) as error:
        loser = error.service

        winner = (
            second_service
            if loser == first_service
            else first_service
        )

        return MatchResult(
            winner=winner,
            loser=loser,
            turns=0,
            technical=True,
            reason=str(error),
        )

    hits = {
        first_session.session_id: set(),
        second_session.session_id: set(),
    }

    shots = {
        first_session.session_id: set(),
        second_session.session_id: set(),
    }

    shot_records = []

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
                hits[opponent.session_id],
                shots[shooter.session_id],
            )

            expected_result = get_expected_shot_result(
                opponent.ships,
                hits[opponent.session_id],
                coordinate,
            )

            shot_records.append(
                ShotRecord(
                    player=shooter.service.name,
                    coordinate=coordinate,
                    expected=expected_result,
                    reported=result,
                )
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
                        shots=shot_records,
                    )

            if result == "miss":
                shooter, opponent = (
                    opponent,
                    shooter,
                )

    except DishonestServiceError as error:
        shot_records.append(
            ShotRecord(
                player=shooter.service.name,
                coordinate=error.coordinate,
                expected=error.expected,
                reported=error.actual,
            )
        )

        loser = error.service

        winner = (
            second_service
            if loser == first_service
            else first_service
        )

        return MatchResult(
            winner=winner,
            loser=loser,
            turns=turns,
            technical=True,
            reason=str(error),
            shots=shot_records,
        )

    except (
        InvalidShotError,
        RepeatedShotError,
        ServiceConnectionError,
        ServiceHTTPError,
        ServiceTimeoutError,
        ServiceResponseError,
    ) as error:
        
        loser = error.service

        winner = (
            second_service
            if loser == first_service
            else first_service
        )

        return MatchResult(
            winner=winner,
            loser=loser,
            turns=turns,
            technical=True,
            reason=str(error),
            shots=shot_records,
        )

    finally:
        close_match_sessions(
            first_session,
            second_session,
        )