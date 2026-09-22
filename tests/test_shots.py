from app.domain.shots import get_shot_result

SHIPS = [
    {"coordinates": ["A1", "A2", "A3"]},
    {"coordinates": ["D5"]},
]

def test_shot_miss():
    result = get_shot_result(
        ships=SHIPS,
        received_shots=[],
        coordinate="J10",
    )

    assert result == "miss"

def test_shot_hit():
    result = get_shot_result(
        ships=SHIPS,
        received_shots=[],
        coordinate="A1",
    )

    assert result == "hit"

def test_shot_killd():
    result = get_shot_result(
        ships=SHIPS,
        received_shots=["A1", "A2"],
        coordinate="A3",
    )

    assert result == "killed"

def test_repeated_shot_does_not_kill_again():
    result = get_shot_result(
        ships=SHIPS,
        received_shots=["A1", "A2", "A3"],
        coordinate="A3"
    )

    assert result == "hit"

def test_single_cell_ship_is_killed_on_first_hit():
    result = get_shot_result(
        ships=SHIPS,
        received_shots=[],
        coordinate="D5",
    )

    assert result == "killed"