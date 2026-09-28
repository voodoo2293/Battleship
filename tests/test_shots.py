from app.domain.shots import (
    choose_shot_coordinate,
    get_available_coordinates,
    get_neighbor_coordinates,
    get_shot_result,
    get_target_coordinates,
)

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

def test_get_available_coordinates_returns_full_board():
    coordinates = get_available_coordinates([])

    assert len(coordinates) == 100
    assert "A1" in coordinates
    assert "J10" in coordinates

def test_get_available_coordinates_excludes_used_coordinates():
    outgoing_shots = [
        {"coordinate": "A1", "result": "miss"},
        {"coordinate": "A2", "result": "hit"},
    ]

    coordinates = get_available_coordinates(outgoing_shots)

    assert "A1" not in coordinates
    assert "A2" not in coordinates
    assert len(coordinates) == 98

def test_get_neighbor_coordinates_for_center_cell():
    neighbors = get_neighbor_coordinates("E5")

    assert set(neighbors) == {
        "D5",
        "F5",
        "E4",
        "E6",
    }

def test_get_neighbor_coordinates_for_corner_cell():
    neighbors = get_neighbor_coordinates("A1")

    assert set(neighbors) == {
        "B1",
        "A2",
    }

def test_get_target_coordinates_after_hit():
    outgoing_shots = [
        {"coordinate": "D5", "result": "hit"},
    ]

    coordinates = get_target_coordinates(outgoing_shots)

    assert set(coordinates) == {
        "C5",
        "E5",
        "D4",
        "D6",
    }

def test_get_target_coordinates_after_hit_and_miss():
    outgoing_shots = [
        {"coordinate": "D5", "result": "hit"},
        {"coordinate": "D6", "result": "miss"},
    ]

    coordinates = get_target_coordinates(outgoing_shots)

    assert "D6" not in coordinates
    assert set(coordinates) == {
        "C5",
        "E5",
        "D4",
    }

def test_get_target_coordinates_after_killed():
    outgoing_shots = [
        {"coordinate": "D5", "result": "hit"},
        {"coordinate": "D6", "result": "killed"},
    ]

    coordinates = get_target_coordinates(outgoing_shots)

    assert coordinates == []

def test_get_traget_coordinates_follows_vertical_hits():
    outgoing_shots = [
        {"coordinate": "D5", "result": "hit"},
        {"coordinate": "D6", "result": "hit"},
    ]

    coordinates = get_target_coordinates(outgoing_shots)

    assert set(coordinates) == {
        "D4",
        "D7",
    }

def test_get_target_coordinates_follows_horizontal_hits():
    outgoing_shots = [
        {"coordinate": "D5", "result": "hit"},
        {"coordinate": "E5", "result": "hit"},
    ]

    coordinates = get_target_coordinates(outgoing_shots)

    assert set(coordinates) == {
        "C5",
        "F5",
    }

def test_choose_shot_coordinate_returns_first_available():
    coordinate = choose_shot_coordinate([])

    assert coordinate == "A1"

def test_choose_shot_coordinate_does_not_repeat_shots():
    outgoing_shots = [
        {"coordinate": "A1", "result": "miss"},
    ]

    coordinate = choose_shot_coordinate(outgoing_shots)

    assert coordinate == "A2"

def test_choose_shot_coordinate_prioritizes_target():
    outgoing_shots = [
        {"coordinate": "D5", "result": "hit"},
    ]

    coordinate = choose_shot_coordinate(outgoing_shots)

    assert coordinate in {
        "C5",
        "E5",
        "D4",
        "D6",
    }